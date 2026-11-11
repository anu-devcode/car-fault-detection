"""Conservative owner guidance. Model scores never establish driving safety."""

from typing import Literal

from pydantic import BaseModel, Field

Symptom = Literal[
    "smoke_or_fire",
    "fuel_smell",
    "brake_problem",
    "steering_problem",
    "overheating",
    "oil_pressure_warning",
    "flashing_engine_light",
    "new_noise",
]

SOURCES = {
    "fire": {
        "title": "US Fire Administration: vehicle fires",
        "url": "https://www.usfa.fema.gov/prevention/vehicle-fires/",
    },
    "warning_lights": {
        "title": "The AA: warning lights",
        "url": "https://www.theaa.com/breakdown-cover/advice/dashboard-warning-lights",
    },
    "manual": {
        "title": "Ford owner manual: warning messages (vehicle-specific)",
        "url": "https://www.fordservicecontent.com/Ford_Content/vdirsnet/OwnerManual/Home/Content?ProcUid=G1592456&Uid=G1592455&buildtype=web&countryCode=USA&div=f&languageCode=en&variantid=4236",
    },
}


class CareRequest(BaseModel):
    fault_class: str | None = Field(default=None, max_length=100)
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    symptoms: list[Symptom] = Field(default_factory=list, max_length=8)


def build_advice(request: CareRequest) -> dict:
    symptoms = set(request.symptoms)
    label = (request.fault_class or "").casefold()
    severity = "inspection"
    heading = "Arrange a mechanic's inspection"
    actions = [
        "Record when the symptom occurs and which warning lights are showing, while safely parked.",
        "Use the owner's manual for your exact vehicle before checking fluid levels or doing maintenance.",
        "Have a qualified mechanic confirm the cause before replacing parts.",
    ]
    avoid = [
        "Do not work near moving belts, hot components, traffic, or high-voltage EV equipment."
    ]
    source_ids = ["warning_lights"]
    if symptoms & {"smoke_or_fire", "fuel_smell"}:
        severity = "emergency"
        heading = "Stop safely and move away from the vehicle"
        actions = [
            "Pull over as soon as it is safe, stop, and switch off the engine.",
            "Get everyone away from the vehicle and traffic; contact local emergency assistance.",
            "Arrange recovery after the immediate danger is handled.",
        ]
        avoid = [
            "Do not restart the vehicle, open the bonnet if fire is suspected, or attempt a repair."
        ]
        source_ids = ["fire"]
    elif symptoms & {"brake_problem", "steering_problem"} or "braking" in label:
        severity = "stop_and_assist"
        heading = "Stop safely and arrange roadside assistance"
        actions = [
            "Bring the vehicle to a safe stop as soon as conditions allow.",
            "Contact roadside assistance or a towing service; describe the brake or steering symptom.",
        ]
        avoid = ["Do not drive to a garage to test a suspected brake or steering fault."]
    elif symptoms & {"overheating", "oil_pressure_warning"}:
        severity = "stop_and_assist"
        heading = "Stop safely and switch off the engine"
        actions = [
            "Once safely stopped, switch off the engine and arrange professional assistance.",
            "Allow the engine to cool; consult your exact owner's manual before any checks.",
        ]
        avoid = [
            "Do not remove a hot cooling-system cap or keep running an engine with an oil-pressure warning."
        ]
        source_ids = ["manual", "warning_lights"]
    elif "flashing_engine_light" in symptoms:
        severity = "stop_and_assist"
        heading = "Stop safely and ask for professional assistance"
        actions = [
            "Stop as soon as it is safe and contact roadside assistance about the flashing warning."
        ]
        avoid = ["Do not keep driving to reproduce a misfire or a flashing engine warning."]
    elif label == "normal" and not symptoms:
        severity = "monitor"
        heading = "No fault identified by this audio model"
        actions = [
            "Continue the maintenance schedule in your exact vehicle's owner's manual.",
            "If there is a warning light, unusual handling, smell, heat, or persistent noise, request an inspection.",
        ]
    uncertain = request.confidence is None or request.confidence < 0.7
    if uncertain and severity == "monitor":
        severity = "inspection"
        heading = "The result is uncertain; arrange an inspection if concerned"
    return {
        "severity": severity,
        "heading": heading,
        "immediate_actions": actions,
        "do_not": avoid,
        "garage_service": "towing"
        if severity in {"emergency", "stop_and_assist"}
        else "car repair",
        "driving_safety": "not_determined",
        "mechanic_confirmation_required": True,
        "model_result_uncertain": uncertain,
        "notice": "Audio classification is a possible pattern, not a confirmed fault or permission to drive. No repair is verified by this app.",
        "sources": [SOURCES[key] for key in source_ids],
        "review_status": "development_guidance_requires_local_mechanic_review",
    }
