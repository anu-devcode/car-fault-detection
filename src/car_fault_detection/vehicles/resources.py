"""Official resource links, without inventing vehicle specifications."""

from pydantic import BaseModel, ConfigDict, Field

# These are owner/manufacturer entry points, not claims of exact imported-vehicle coverage.
MANUFACTURERS = {
    "toyota": "https://www.toyota.com/owners/resources/warranty-owners-manuals/",
    "hyundai": "https://www.hyundai.com/worldwide/en/",
    "suzuki": "https://www.globalsuzuki.com/automobile/",
    "nissan": "https://www.nissan-global.com/EN/",
    "honda": "https://global.honda/en/",
    "ford": "https://www.ford.com/support/owner-manuals/",
    "byd": "https://www.byd.com/",
    "volkswagen": "https://www.volkswagen.com/",
    "bmw": "https://www.bmw.com/",
    "mercedes-benz": "https://www.mercedes-benz.com/",
    "kia": "https://worldwide.kia.com/",
    "mitsubishi": "https://www.mitsubishi-motors.com/",
    "isuzu": "https://www.isuzu.co.jp/world/",
    "subaru": "https://www.subaru-global.com/",
    "tesla": "https://www.tesla.com/ownersmanual",
    "geely": "https://global.geely.com/",
    "chery": "https://www.cheryinternational.com/",
    "renault": "https://www.renault.com/",
}


class VehicleProfile(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    make: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=100)
    year: int | None = Field(default=None, ge=1900, le=2030)


def owner_resources(profile: VehicleProfile) -> dict:
    make = profile.make.strip().casefold()
    make = {"mercedes": "mercedes-benz", "vw": "volkswagen"}.get(make, make)
    url = MANUFACTURERS.get(make)
    return {
        "vehicle": profile.model_dump(),
        "identity_status": "user_provided_not_independently_verified",
        "resources": [{"title": "Manufacturer / owner resources", "url": url}] if url else [],
        "unknown_fields": [
            "trim",
            "engine",
            "VIN",
            "service_history",
            "mileage",
            "hidden_damage",
            "exact_maintenance_intervals",
        ],
        "maintenance_topics": [
            "Exact owner manual and service schedule",
            "Tyre pressures on the vehicle placard",
            "Warning lights and fluid checks",
            "Service records and outstanding recalls via the manufacturer",
        ],
        "notice": "Confirm the market, VIN and specification of your Ethiopian import before following a manual. Some linked portals cover a specific market. No specifications or repair instructions are inferred from a photo.",
    }
