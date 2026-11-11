from fastapi import APIRouter

from car_fault_detection.care.guidance import CareRequest, build_advice

router = APIRouter(prefix="/care", tags=["care"])


@router.post("/triage")
def triage(request: CareRequest):
    return build_advice(request)
