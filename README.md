# SafeVillage backend

The full setup, demo script, tests, and deployment notes are in the project README:

`../README.md`

Quick start from this folder in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
pytest
```

Then open http://127.0.0.1:8000 and http://127.0.0.1:8000/docs.

Do not commit `.env` or the SQLite database. Demo accounts and sample schemes are labelled and are not official government records.
