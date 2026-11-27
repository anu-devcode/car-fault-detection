from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from car_fault_detection.vehicles.inspection import InspectionBusy, InspectionUnavailable
from car_fault_detection.vehicles.resources import VehicleProfile, owner_resources

router = APIRouter(prefix="/vehicles", tags=["vehicles"])
MAX_PHOTO_BYTES = 8 * 1024 * 1024


@router.get("/vision/status")
def vision_status(request: Request):
    return {
        "ready": request.app.state.vehicle_recognizer is not None,
        "inspection_configured": request.app.state.photo_inspector is not None,
        "confirmation_required": True,
    }


async def read_photo(file: UploadFile) -> bytes:
    try:
        content = await file.read(MAX_PHOTO_BYTES + 1)
    finally:
        await file.close()
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(413, "Photo exceeds the 8 MB limit.")
    return content


@router.post("/identify")
async def identify(request: Request, file: UploadFile = File(...)):
    recognizer = request.app.state.vehicle_recognizer
    if recognizer is None:
        await file.close()
        raise HTTPException(
            503, "Photo recognition is not configured. Manual vehicle entry is available."
        )
    content = await read_photo(file)
    try:
        return await run_in_threadpool(recognizer.predict, content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/inspect")
async def inspect(request: Request, file: UploadFile = File(...)):
    inspector = request.app.state.photo_inspector
    if inspector is None:
        await file.close()
        raise HTTPException(503, "Photo inspection is not configured. Use the symptom check.")
    content = await read_photo(file)
    try:
        return await run_in_threadpool(inspector.inspect, content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except InspectionBusy as exc:
        raise HTTPException(429, str(exc), headers={"Retry-After": "5"}) from exc
    except InspectionUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@router.post("/resources")
def resources(profile: VehicleProfile):
    return owner_resources(profile)
