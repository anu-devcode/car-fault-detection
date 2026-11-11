from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from car_fault_detection.vehicles.resources import VehicleProfile, owner_resources

router = APIRouter(prefix="/vehicles", tags=["vehicles"])
MAX_PHOTO_BYTES = 8 * 1024 * 1024


@router.get("/vision/status")
def vision_status(request: Request):
    return {
        "ready": request.app.state.vehicle_recognizer is not None,
        "confirmation_required": True,
    }


@router.post("/identify")
async def identify(request: Request, file: UploadFile = File(...)):
    recognizer = request.app.state.vehicle_recognizer
    if recognizer is None:
        raise HTTPException(
            503, "Photo recognition is not configured. Manual vehicle entry is available."
        )
    try:
        content = await file.read(MAX_PHOTO_BYTES + 1)
    finally:
        await file.close()
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(413, "Photo exceeds the 8 MB limit.")
    try:
        return await run_in_threadpool(recognizer.predict, content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/resources")
def resources(profile: VehicleProfile):
    return owner_resources(profile)
