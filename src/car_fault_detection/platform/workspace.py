"""Role-filtered workspaces, garage search and assistance request transitions."""

import math
import secrets
import uuid
from collections import defaultdict
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import and_, func, insert, select, update
from sqlalchemy.exc import IntegrityError

from car_fault_detection.platform.access import (
    check_origin,
    database,
    digest,
    need_account,
    normalize_email,
    public_account,
    require_role,
    timestamp,
)
from car_fault_detection.platform.database import accounts, garages, invites, jobs

router = APIRouter(prefix="/platform", tags=["assistance"])
driver = require_role("driver")
mechanic = require_role("mechanic")
admin = require_role("admin")
same_origin = [Depends(check_origin)]
CITY = "Addis Ababa"
RADIUS_KM = 25
Service = Literal["inspection", "breakdown", "maintenance", "tyres", "electrical", "other"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Location(Input):
    latitude: float | None = Field(default=None, ge=-85, le=85)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def check_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Supply both coordinates or leave both blank.")
        return self


class DirectoryQuery(Location):
    city: str = Field(default="", max_length=80)


class GarageEntry(Location):
    id: UUID | None = None
    name: str = Field(min_length=2, max_length=100)
    city: str = Field(min_length=2, max_length=80)
    area: str = Field(min_length=2, max_length=140)
    phone: str = Field(pattern=r"^\+?[0-9]{7,15}$")
    published: bool = False


class InviteEntry(Input):
    garage_id: UUID
    email: str = Field(max_length=254)
    _validate_email = field_validator("email")(normalize_email)


class Availability(Input):
    available: bool


class NewRequest(Input):
    mechanic_id: UUID
    request_key: UUID
    service: Service
    details: str = Field(min_length=5, max_length=1000)
    callback: str | None = Field(default=None, pattern=r"^\+?[0-9]{7,15}$")


class StatusChange(Input):
    status: Literal["accepted", "declined", "completed", "cancelled"]


@router.post("/directory/search", dependencies=same_origin)
def directory(query: DirectoryQuery, _=Depends(driver), db=Depends(database)):
    statement = select(garages).where(garages.c.published.is_(True))
    location = query.latitude is not None
    if query.city or not location:
        statement = statement.where(garages.c.city_key == (query.city or CITY).casefold())
    if location:
        # Bounding box keeps unrelated rows out of the application distance calculation.
        lat_delta = RADIUS_KM / 110
        lon_delta = lat_delta / math.cos(math.radians(abs(query.latitude) + lat_delta))
        statement = statement.where(
            garages.c.latitude.between(query.latitude - lat_delta, query.latitude + lat_delta)
        )
        low, high = query.longitude - lon_delta, query.longitude + lon_delta
        if low < -180:
            statement = statement.where(
                (garages.c.longitude >= low + 360) | (garages.c.longitude <= high)
            )
        elif high > 180:
            statement = statement.where(
                (garages.c.longitude >= low) | (garages.c.longitude <= high - 360)
            )
        else:
            statement = statement.where(garages.c.longitude.between(low, high))
    # Stable nearest-neighbour approximation in SQL, followed by exact great-circle distance.
    if location:
        dlat = garages.c.latitude - query.latitude
        dlon = func.abs(garages.c.longitude - query.longitude)
        wrapped = 180 - func.abs(dlon - 180)
        weight = math.cos(math.radians(query.latitude)) ** 2
        statement = statement.order_by(dlat * dlat + weight * wrapped * wrapped)
    else:
        statement = statement.order_by(garages.c.name)
    rows = []
    for garage in db.execute(statement.limit(80)).mappings():
        distance = None
        if location:
            distance = great_circle(
                query.latitude, query.longitude, garage["latitude"], garage["longitude"]
            )
            if distance > RADIUS_KM:
                continue
        rows.append(
            {
                **public_garage(garage),
                "distance_km": round(distance, 1) if distance is not None else None,
            }
        )
    if location:
        rows.sort(key=lambda item: item["distance_km"])
    rows = rows[:20]
    people = defaultdict(list)
    if rows:
        for row in db.execute(
            select(accounts.c.id, accounts.c.name, accounts.c.garage_id)
            .where(
                accounts.c.role == "mechanic",
                accounts.c.available.is_(True),
                accounts.c.garage_id.in_([item["id"] for item in rows]),
            )
            .order_by(accounts.c.name)
        ).mappings():
            people[row["garage_id"]].append({"id": row["id"], "name": row["name"]})
    return {
        "garages": [dict(row, mechanics=people[row["id"]][:20]) for row in rows],
        "radius_km": RADIUS_KM if location else None,
    }


def public_garage(row):
    return {
        key: row[key]
        for key in ("id", "name", "city", "area", "phone", "latitude", "longitude", "published")
    }


def great_circle(latitude, longitude, other_latitude, other_longitude):
    lat1, lat2 = math.radians(latitude), math.radians(other_latitude)
    delta = math.radians(other_longitude - longitude)
    point = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta / 2) ** 2
    )
    return 6371.0 * 2 * math.asin(math.sqrt(min(1, point)))


def counts_for(db, condition):
    return dict(
        db.execute(
            select(jobs.c.status, func.count()).where(condition).group_by(jobs.c.status)
        ).all()
    )


@router.get("/workspace")
def workspace(account=Depends(need_account), db=Depends(database)):
    role, account_id = account["role"], account["id"]
    result = {"account": public_account(account)}
    if role == "admin":
        garage_rows = db.execute(select(garages).order_by(garages.c.name).limit(200)).mappings()
        roster = db.execute(
            select(accounts.c.id, accounts.c.name, accounts.c.garage_id, accounts.c.available)
            .where(
                accounts.c.role == "mechanic",
            )
            .order_by(accounts.c.name)
            .limit(200)
        ).mappings()
        return {
            **result,
            "garages": [public_garage(row) for row in garage_rows],
            "mechanics": [dict(row) for row in roster],
            "stats": {
                "published": db.scalar(
                    select(func.count()).select_from(garages).where(garages.c.published.is_(True))
                ),
                "available": db.scalar(
                    select(func.count())
                    .select_from(accounts.join(garages))
                    .where(
                        accounts.c.role == "mechanic",
                        accounts.c.available.is_(True),
                        garages.c.published.is_(True),
                    )
                ),
                "open": db.scalar(
                    select(func.count())
                    .select_from(jobs)
                    .where(jobs.c.status.in_(["requested", "accepted"]))
                ),
            },
        }
    actor_column = jobs.c.driver_id if role == "driver" else jobs.c.mechanic_id
    counterpart_column = jobs.c.mechanic_id if role == "driver" else jobs.c.driver_id
    rows = db.execute(
        select(
            jobs.c.id,
            jobs.c.service,
            jobs.c.details,
            jobs.c.callback,
            jobs.c.status,
            jobs.c.created_at,
            jobs.c.updated_at,
            garages.c.name.label("garage"),
            garages.c.phone.label("garage_phone"),
            garages.c.published,
            accounts.c.name.label("counterpart"),
        )
        .select_from(jobs)
        .join(garages, garages.c.id == jobs.c.garage_id)
        .join(accounts, accounts.c.id == counterpart_column)
        .where(actor_column == account_id)
        .order_by(jobs.c.created_at.desc(), jobs.c.id)
        .limit(50)
    ).mappings()
    requests = []
    for row in rows:
        item = dict(row)
        if not item.pop("published"):
            item.pop("garage_phone")
        if role == "mechanic" and row["status"] != "accepted":
            item.pop("callback")
        requests.append(item)
    result.update(requests=requests, counts=counts_for(db, actor_column == account_id))
    if role == "mechanic":
        garage = (
            db.execute(select(garages).where(garages.c.id == account["garage_id"])).mappings().one()
        )
        result["garage"] = public_garage(garage)
    return result


@router.post("/admin/garages", dependencies=same_origin)
def save_garage(entry: GarageEntry, _=Depends(admin), db=Depends(database)):
    values = entry.model_dump(exclude={"id"})
    values["city_key"] = entry.city.casefold()
    if entry.id:
        garage_id = str(entry.id)
        update_result = db.execute(
            update(garages).where(garages.c.id == garage_id).values(**values)
        )
        if not update_result.rowcount:
            raise HTTPException(404, "Garage not found.")
    else:
        garage_id = str(uuid.uuid4())
        db.execute(insert(garages).values(**values, id=garage_id))
    db.commit()
    return {"id": garage_id}


@router.post("/admin/invitations", dependencies=same_origin, status_code=201)
def create_invite(entry: InviteEntry, _=Depends(admin), db=Depends(database)):
    garage_id = str(entry.garage_id)
    if not db.scalar(select(garages.c.id).where(garages.c.id == garage_id)):
        raise HTTPException(404, "Garage not found.")
    if db.scalar(select(accounts.c.id).where(accounts.c.email == entry.email)):
        raise HTTPException(409, "This email already has an account.")
    token = secrets.token_urlsafe(32)
    expires_at = timestamp() + 24 * 60 * 60
    db.execute(
        insert(invites).values(
            token_hash=digest(token), email=entry.email, garage_id=garage_id, expires_at=expires_at
        )
    )
    db.commit()
    return {"code": token, "expires_at": expires_at}


@router.post("/mechanic/availability", dependencies=same_origin)
def set_availability(entry: Availability, account=Depends(mechanic), db=Depends(database)):
    db.execute(
        update(accounts).where(accounts.c.id == account["id"]).values(available=entry.available)
    )
    db.commit()
    return {"available": entry.available}


@router.post("/requests", dependencies=same_origin, status_code=201)
def submit_request(entry: NewRequest, account=Depends(driver), db=Depends(database)):
    lookup = select(jobs.c.id).where(
        and_(
            jobs.c.driver_id == account["id"],
            jobs.c.request_key == str(entry.request_key),
        )
    )
    request_id = db.scalar(lookup)
    if request_id:
        return {"id": request_id}
    mechanic_id = str(entry.mechanic_id)
    garage_id = db.scalar(
        select(accounts.c.garage_id)
        .join(garages)
        .where(
            accounts.c.id == mechanic_id,
            accounts.c.role == "mechanic",
            accounts.c.available.is_(True),
            garages.c.published.is_(True),
        )
        .with_for_update()
    )
    if not garage_id:
        raise HTTPException(409, "That mechanic is unavailable. Refresh your garage search.")
    request_id = str(uuid.uuid4())
    now = timestamp()
    try:
        db.execute(
            insert(jobs).values(
                **entry.model_dump(exclude={"mechanic_id", "request_key"}),
                id=request_id,
                request_key=str(entry.request_key),
                mechanic_id=mechanic_id,
                garage_id=garage_id,
                driver_id=account["id"],
                status="requested",
                created_at=now,
                updated_at=now,
            )
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(lookup)
        if not existing:
            raise
        return {"id": existing}
    return {"id": request_id}


@router.post("/requests/{request_id}/status", dependencies=same_origin)
def change_status(
    request_id: UUID, entry: StatusChange, account=Depends(need_account), db=Depends(database)
):
    new_status = entry.status
    if account["role"] == "driver" and new_status == "cancelled":
        owner = jobs.c.driver_id
        previous = ["requested", "accepted"]
    elif account["role"] == "mechanic" and new_status in {"accepted", "declined", "completed"}:
        owner = jobs.c.mechanic_id
        previous = ["accepted"] if new_status == "completed" else ["requested"]
    else:
        raise HTTPException(403, "This action is unavailable for your account.")
    selected = (jobs.c.id == str(request_id), owner == account["id"])
    changed = db.execute(
        update(jobs)
        .where(*selected, jobs.c.status.in_(previous))
        .values(
            status=new_status,
            updated_at=timestamp(),
        )
    )
    if not changed.rowcount:
        if db.scalar(select(jobs.c.id).where(*selected)) is None:
            raise HTTPException(404, "Request not found.")
        raise HTTPException(409, "The request status has changed. Refresh and try again.")
    db.commit()
    return {"status": new_status}
