"""Account registration, bounded login attempts and database-backed sessions."""

import hashlib
import secrets
import time
import uuid

from argon2 import PasswordHasher, exceptions
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError

from car_fault_detection.platform.database import accounts, invites, limits, sessions

router = APIRouter(prefix="/access")
SESSION_AGE = 12 * 60 * 60
hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
dummy_hash = hasher.hash(secrets.token_urlsafe(24))


def timestamp():
    return int(time.time())


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def database(request: Request):
    engine = request.app.state.platform_engine
    if engine is None:
        raise HTTPException(503, "The assistance workspace is not configured.")
    with engine.connect() as connection:
        yield connection


def cookie_name(request):
    return (
        "__Host-vehicle_session" if request.app.state.secure_platform_cookie else "vehicle_session"
    )


def session_hash(request):
    token = request.cookies.get(cookie_name(request))
    if token and len(token) == 43:
        return digest(token)
    return None


def public_account(account):
    if account is None:
        return None
    return {key: account[key] for key in ("id", "name", "role", "garage_id", "available")}


def session_account(request: Request, db=Depends(database)):
    return (
        db.execute(
            select(accounts)
            .join(sessions, accounts.c.id == sessions.c.account_id)
            .where(
                sessions.c.token_hash == session_hash(request), sessions.c.expires_at > timestamp()
            )
        )
        .mappings()
        .first()
    )


def need_account(account=Depends(session_account)):
    if account is None:
        raise HTTPException(401, "Sign in to continue.")
    return account


def require_role(role):
    def check(account=Depends(need_account)):
        if account["role"] != role:
            raise HTTPException(403, "This action is unavailable for your account.")
        return account

    return check


def check_origin(request: Request):
    if request.headers.get("origin") != request.app.state.platform_web_origin:
        raise HTTPException(403, "Request origin was not accepted.")


def normalize_email(value):
    value = value.strip().lower()
    local, separator, domain = value.partition("@")
    if (
        not separator
        or not local
        or "." not in domain
        or "@" in domain
        or any(c.isspace() for c in value)
    ):
        raise ValueError("Enter a valid email address.")
    return value


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)
    _validate_email = field_validator("email")(normalize_email)


class Registration(Credentials):
    name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=12, max_length=128)
    invite: str | None = Field(default=None, min_length=43, max_length=43)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value):
        return value.strip() if isinstance(value, str) else value


def throttle_auth(db, action, email):
    bucket = timestamp() // 900
    upsert = pg_insert if db.dialect.name == "postgresql" else sqlite_insert
    attempt = upsert(limits).values(key=digest(f"{action}:{email}"), bucket=bucket, attempts=1)
    count = db.execute(
        attempt.on_conflict_do_update(
            index_elements=["key", "bucket"], set_={"attempts": limits.c.attempts + 1}
        ).returning(limits.c.attempts)
    ).scalar_one()
    db.execute(delete(limits).where(limits.c.bucket < bucket - 2))
    db.commit()
    if count > 8:
        raise HTTPException(
            429, "Too many attempts. Try again in 15 minutes.", headers={"Retry-After": "900"}
        )


def start_session(request, response, db, account_id):
    token = secrets.token_urlsafe(32)
    db.execute(delete(sessions).where(sessions.c.expires_at <= timestamp()))
    old = session_hash(request)
    if old:
        db.execute(delete(sessions).where(sessions.c.token_hash == old))
    db.execute(
        insert(sessions).values(
            token_hash=digest(token), account_id=account_id, expires_at=timestamp() + SESSION_AGE
        )
    )
    db.commit()
    response.set_cookie(
        cookie_name(request),
        token,
        max_age=SESSION_AGE,
        httponly=True,
        secure=request.app.state.secure_platform_cookie,
        samesite="lax",
        path="/",
    )


@router.get("/session")
def read_session(account=Depends(session_account)):
    return {"account": public_account(account)}


@router.post("/register", dependencies=[Depends(check_origin)], status_code=201)
def register(payload: Registration, request: Request, response: Response, db=Depends(database)):
    throttle_auth(db, "register", payload.email)
    # Hash before taking the one-use invite row lock.
    password_hash = hasher.hash(payload.password)
    garage_id = None
    if payload.invite:
        garage_id = db.execute(
            update(invites)
            .where(
                invites.c.token_hash == digest(payload.invite),
                invites.c.email == payload.email,
                invites.c.expires_at > timestamp(),
                invites.c.used.is_(False),
            )
            .values(used=True)
            .returning(invites.c.garage_id)
        ).scalar_one_or_none()
        if not garage_id:
            raise HTTPException(400, "The invitation is invalid, expired, or already used.")
    account = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "role": "mechanic" if garage_id else "driver",
        "garage_id": garage_id,
        "available": False,
    }
    try:
        db.execute(
            insert(accounts).values(**account, email=payload.email, password_hash=password_hash)
        )
        start_session(request, response, db, account["id"])
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            409, "This account could not be created. If you already registered, sign in."
        ) from exc
    return {"account": account}


@router.post("/login", dependencies=[Depends(check_origin)])
def login(payload: Credentials, request: Request, response: Response, db=Depends(database)):
    throttle_auth(db, "login", payload.email)
    account = (
        db.execute(select(accounts).where(accounts.c.email == payload.email)).mappings().first()
    )
    try:
        hasher.verify(account["password_hash"] if account else dummy_hash, payload.password)
    except (exceptions.VerificationError, exceptions.InvalidHashError):
        raise HTTPException(401, "Email or password is incorrect.") from None
    if not account:
        raise HTTPException(401, "Email or password is incorrect.")
    start_session(request, response, db, account["id"])
    return {"account": public_account(account)}


@router.post("/logout", dependencies=[Depends(check_origin)])
def logout(request: Request, response: Response, db=Depends(database)):
    db.execute(delete(sessions).where(sessions.c.token_hash == session_hash(request)))
    db.commit()
    response.delete_cookie(
        cookie_name(request),
        path="/",
        secure=request.app.state.secure_platform_cookie,
        httponly=True,
        samesite="lax",
    )
    return {"account": None}
