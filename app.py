"""Compatibility entry point for `streamlit run app.py`."""

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).parent / "apps" / "streamlit_app.py"), run_name="__main__")
