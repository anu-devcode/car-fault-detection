"""Create the assistance database tables and provision a local operator account."""

import argparse
import getpass
import os
import uuid

from sqlalchemy import insert

from car_fault_detection.platform.access import Registration, hasher
from car_fault_detection.platform.database import accounts, open_engine, schema


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("init", help="Create the initial database schema.")
    admin = actions.add_parser("admin", help="Provision an administrator.")
    admin.add_argument("--email", required=True)
    admin.add_argument("--name", required=True)
    args = parser.parse_args()
    url = os.environ.get("PLATFORM_DATABASE_URL")
    if not url:
        parser.error("Set PLATFORM_DATABASE_URL before running setup.")
    engine = open_engine(url)
    try:
        if args.action == "init":
            schema.create_all(engine)
            print("Assistance schema is ready.")
        else:
            password = getpass.getpass("New administrator password: ")
            if password != getpass.getpass("Confirm password: "):
                parser.error("Passwords did not match.")
            value = Registration(email=args.email, name=args.name, password=password)
            with engine.begin() as db:
                db.execute(
                    insert(accounts).values(
                        id=str(uuid.uuid4()),
                        email=value.email,
                        name=value.name,
                        password_hash=hasher.hash(value.password),
                        role="admin",
                        available=False,
                    )
                )
            print("Administrator account created.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
