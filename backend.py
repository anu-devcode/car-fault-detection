"""Compatibility entry point; implementation lives in car_fault_detection.api.app."""

from car_fault_detection.api.app import *  # noqa: F403

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
