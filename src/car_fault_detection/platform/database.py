"""Persistence for the assistance platform. Schema installation is explicit."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.engine import make_url

schema = MetaData()
garages = Table(
    "garages",
    schema,
    Column("id", String(36), primary_key=True),
    Column("name", String(100), nullable=False),
    Column("city", String(80), nullable=False),
    Column("city_key", String(80), nullable=False, index=True),
    Column("area", String(140), nullable=False),
    Column("phone", String(20), nullable=False),
    Column("latitude", Float, index=True),
    Column("longitude", Float),
    Column("published", Boolean, nullable=False),
)
accounts = Table(
    "accounts",
    schema,
    Column("id", String(36), primary_key=True),
    Column("name", String(80), nullable=False),
    Column("email", String(254), nullable=False, unique=True),
    Column("password_hash", String(255), nullable=False),
    Column("role", String(12), nullable=False),
    Column("garage_id", ForeignKey("garages.id"), index=True),
    Column("available", Boolean, nullable=False, default=False),
    CheckConstraint("role IN ('driver', 'mechanic', 'admin')"),
    CheckConstraint(
        "(role = 'mechanic' AND garage_id IS NOT NULL) OR (role <> 'mechanic' AND garage_id IS NULL)"
    ),
)
sessions = Table(
    "platform_sessions",
    schema,
    Column("token_hash", String(64), primary_key=True),
    Column("account_id", ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("expires_at", BigInteger, nullable=False, index=True),
)
invites = Table(
    "mechanic_invites",
    schema,
    Column("token_hash", String(64), primary_key=True),
    Column("email", String(254), nullable=False),
    Column("garage_id", ForeignKey("garages.id"), nullable=False),
    Column("expires_at", BigInteger, nullable=False),
    Column("used", Boolean, nullable=False, default=False),
)
limits = Table(
    "platform_auth_limits",
    schema,
    Column("key", String(64), primary_key=True),
    Column("bucket", BigInteger, primary_key=True, index=True),
    Column("attempts", Integer, nullable=False),
)
jobs = Table(
    "assistance_requests",
    schema,
    Column("id", String(36), primary_key=True),
    Column("request_key", String(36), nullable=False),
    Column("driver_id", ForeignKey("accounts.id"), nullable=False),
    Column("mechanic_id", ForeignKey("accounts.id"), nullable=False),
    Column("garage_id", ForeignKey("garages.id"), nullable=False),
    Column("service", String(24), nullable=False),
    Column("details", String(1000), nullable=False),
    Column("callback", String(20)),
    Column("status", String(16), nullable=False),
    Column("created_at", BigInteger, nullable=False),
    Column("updated_at", BigInteger, nullable=False),
    UniqueConstraint("driver_id", "request_key"),
    Index("ix_requests_driver_created", "driver_id", "created_at"),
    Index("ix_requests_mechanic_created", "mechanic_id", "created_at"),
    CheckConstraint("status IN ('requested', 'accepted', 'declined', 'completed', 'cancelled')"),
)


def open_engine(value):
    url = make_url(value)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+psycopg")
    if url.drivername not in {"sqlite", "postgresql+psycopg"}:
        raise ValueError("Use sqlite or PostgreSQL for PLATFORM_DATABASE_URL")
    if url.drivername == "sqlite":
        if not url.database or url.database == ":memory:":
            raise ValueError("Use a file-backed SQLite database for development")
        engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 8})

        @event.listens_for(engine, "connect")
        def enforce_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        return engine
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5, pool_timeout=5)
