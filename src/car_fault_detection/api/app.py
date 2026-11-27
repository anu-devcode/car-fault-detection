"""FastAPI transport adapter; inference and audio processing live in separate modules."""

import logging
import os
import tempfile
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from car_fault_detection import config
from car_fault_detection.api.care import router as care_router
from car_fault_detection.api.vehicles import router as vehicle_router
from car_fault_detection.care.guidance import CareRequest, build_advice
from car_fault_detection.platform.access import router as platform_access_router
from car_fault_detection.platform.database import open_engine

logger = logging.getLogger(__name__)
MAX_AUDIO_SIZE_BYTES = 5 * 1024 * 1024
MIN_AUDIO_SIZE_BYTES = 1024
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".webm", ".opus"}


def load_detector():
    backend = os.environ.get("AUDIO_MODEL_BACKEND", "crnn")
    if backend in {"research_ast", "research_crnn"}:
        if os.environ.get("ALLOW_RESEARCH_MODELS") != "true":
            raise ValueError("Research audio models require explicit local opt-in")
        from car_fault_detection.ml.research_inference import ResearchAudioDetector

        default_directory = (
            "research/transfer-comparison"
            if backend == "research_ast"
            else "data/research/crnn-windows-3"
        )
        return ResearchAudioDetector(
            os.environ.get("RESEARCH_AUDIO_MODEL_DIR", default_directory),
            encoder=backend.removeprefix("research_"),
        )
    # Keep imports lazy so health/configuration tools do not initialize PyTorch.
    from car_fault_detection.ml.inference import EngineFaultDetector

    return EngineFaultDetector(
        os.path.join(config.MODELS_DIR, "best_model.pth"),
        os.path.join(config.MODELS_DIR, "label_encoder.joblib"),
    )


def load_vehicle_recognizer():
    directory = os.environ.get("VISION_MODEL_DIR")
    if not directory:
        return None
    from car_fault_detection.vehicles.vision import VehicleRecognizer

    return VehicleRecognizer(directory)


def load_photo_inspector():
    model = os.environ.get("PHOTO_INSPECTION_MODEL")
    if not model:
        return None
    from car_fault_detection.vehicles.inspection import PhotoInspector

    return PhotoInspector(model)


def create_app(
    detector_factory: Callable = load_detector,
    vehicle_factory: Callable = load_vehicle_recognizer,
    inspection_factory: Callable = load_photo_inspector,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        try:
            application.state.detector = await run_in_threadpool(detector_factory)
        except Exception:
            logger.exception("Model initialization failed; prediction service is unavailable")
            application.state.detector = None
        try:
            application.state.vehicle_recognizer = await run_in_threadpool(vehicle_factory)
        except Exception:
            logger.exception("Photo model initialization failed; manual vehicle entry is available")
            application.state.vehicle_recognizer = None
        try:
            application.state.photo_inspector = await run_in_threadpool(inspection_factory)
        except Exception:
            logger.exception("Photo inspection initialization failed")
            application.state.photo_inspector = None
        yield
        application.state.detector = None
        application.state.vehicle_recognizer = None
        application.state.photo_inspector = None
        if application.state.platform_engine is not None:
            await run_in_threadpool(application.state.platform_engine.dispose)

    application = FastAPI(
        title="Car Engine Fault Detection API", version="0.2.0", lifespan=lifespan
    )
    application.state.detector = None
    application.state.vehicle_recognizer = None
    application.state.photo_inspector = None
    database_url = os.environ.get("PLATFORM_DATABASE_URL")
    application.state.platform_engine = open_engine(database_url) if database_url else None
    web_origin = os.environ.get("PLATFORM_WEB_ORIGIN", "http://localhost:3000")
    parsed_origin = urlsplit(web_origin)
    if database_url and (
        not parsed_origin.netloc
        or web_origin != f"{parsed_origin.scheme}://{parsed_origin.netloc}"
        or parsed_origin.username
        or (
            parsed_origin.scheme != "https"
            and web_origin not in {"http://localhost:3000", "http://127.0.0.1:3000"}
        )
    ):
        raise ValueError("Set PLATFORM_WEB_ORIGIN to the exact HTTPS frontend origin.")
    application.state.platform_web_origin = web_origin
    application.state.secure_platform_cookie = parsed_origin.scheme == "https"
    application.include_router(care_router)
    application.include_router(vehicle_router)
    application.include_router(platform_access_router, prefix="/platform", tags=["assistance"])
    origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        if request.url.path.startswith("/platform/"):
            # Validation responses must not echo credentials or driver's notes.
            return JSONResponse(
                {"detail": "Check the submitted fields and try again."}, status_code=422
            )
        return await request_validation_exception_handler(request, exc)

    @application.middleware("http")
    async def protect_workspace_responses(request: Request, call_next):
        if not request.url.path.startswith("/platform/"):
            return await call_next(request)
        if (
            request.method == "POST"
            and request.headers.get("content-length", "").isdigit()
            and int(request.headers["content-length"]) > 8192
        ):
            response = JSONResponse({"detail": "Request is too large."}, status_code=413)
        else:
            response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def require_detector():
        detector = application.state.detector
        if detector is None:
            raise HTTPException(status_code=503, detail="Prediction service is unavailable.")
        return detector

    @application.get("/")
    @application.get("/health")
    async def health():
        return {
            "status": "running",
            "model_backend": os.environ.get("AUDIO_MODEL_BACKEND", "crnn"),
            "model": "loaded" if application.state.detector is not None else "not loaded",
            "message": "Car Engine Fault Detection API",
        }

    @application.get("/ready")
    async def ready():
        require_detector()
        return {"status": "ready", "model": "loaded"}

    @application.get("/classes")
    async def classes():
        detector = require_detector()
        return {"classes": list(detector.classes), "fault_mapping": config.FAULT_MAPPING}

    @application.post("/predict")
    async def predict(file: UploadFile = File(...)):
        detector = require_detector()
        suffix = Path(file.filename or "").suffix.lower()
        content_type = (file.content_type or "").lower()
        if suffix not in ALLOWED_AUDIO_EXTENSIONS and not content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Unsupported audio file type.")
        try:
            contents = await file.read(MAX_AUDIO_SIZE_BYTES + 1)
        finally:
            await file.close()
        if len(contents) > MAX_AUDIO_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Audio file exceeds the 5 MB limit.")
        if len(contents) < MIN_AUDIO_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="Audio file is too small or empty.")
        try:
            # Context-managed directory removes uploads even if decoding/inference fails.
            with tempfile.TemporaryDirectory(prefix="car-fault-") as directory:
                audio_path = Path(directory) / (
                    "recording" + (suffix if suffix in ALLOWED_AUDIO_EXTENSIONS else ".wav")
                )
                audio_path.write_bytes(contents)
                prediction = await run_in_threadpool(detector.predict_details, str(audio_path))
            return {
                "success": True,
                "fault_class": prediction.fault_class.replace("_", " ").title(),
                "location": prediction.location,
                "is_normal": prediction.fault_class.casefold() == "normal",
                "confidence": prediction.confidence,
                "advice": build_advice(
                    CareRequest(
                        fault_class=prediction.fault_class, confidence=prediction.confidence
                    )
                ),
            }
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Unable to decode valid audio.") from exc
        except Exception as exc:
            logger.exception("Prediction failed")
            raise HTTPException(status_code=500, detail="Audio analysis failed.") from exc

    return application


app = create_app()
