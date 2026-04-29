# Smart Car Fault Detection

Minimal and clear starter structure for an audio-based car fault detection pipeline.

## Project Structure

```
car_fault_detection/
├── data/
│   ├── raw/
│   └── processed/
├── preprocessing.py
├── feature_extraction.py
├── train_model.py
├── evaluate.py
├── app.py
├── requirements.txt
└── README.md
```

## Setup (Windows PowerShell)

1. Create virtual environment
   - `python -m venv .venv`
2. Activate
   - `.\\.venv\\Scripts\\Activate.ps1`
3. Install dependencies
   - `python -m pip install --upgrade pip`
   - `pip install -r requirements.txt`

## Data Placeholder

Put your raw audio dataset in `data/raw/` with class folders like:

- `data/raw/normal/*.wav`
- `data/raw/misfire/*.wav`
- `data/raw/knocking/*.wav`
- `data/raw/belt_issue/*.wav`

## Run Order

1. `python preprocessing.py`
2. `python feature_extraction.py`
3. `python train_model.py`
4. `python evaluate.py`

Optional demo:

- `python app.py`
