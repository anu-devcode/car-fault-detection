"""FastAPI transport adapter; inference and audio processing live in separate modules."""

import logging
import os
import tempfile
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from car_fault_detection import config
from car_fault_detection.api.care import router as care_router
from car_fault_detection.care.guidance import CareRequest, build_advice

logger = logging.getLogger(__name__)
MAX_AUDIO_SIZE_BYTES = 5 * 1024 * 1024
MIN_AUDIO_SIZE_BYTES = 1024
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".webm", ".opus"}


def load_detector():
    # Keep imports lazy so health/configuration tools do not initialize PyTorch.
    from car_fault_detection.ml.inference import EngineFaultDetector

    return EngineFaultDetector(
        os.path.join(config.MODELS_DIR, "best_model.pth"),
        os.path.join(config.MODELS_DIR, "label_encoder.joblib"),
    )


def create_app(detector_factory: Callable = load_detector) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        try:
            application.state.detector = await run_in_threadpool(detector_factory)
        except Exception:
            logger.exception("Model initialization failed; prediction service is unavailable")
            application.state.detector = None
        yield
        application.state.detector = None

    application = FastAPI(
        title="Car Engine Fault Detection API", version="0.2.0", lifespan=lifespan
    )
    application.state.detector = None
    application.include_router(care_router)
    origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

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
