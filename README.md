# Knight Cash API Audit

This project contains a corrected FastAPI implementation and a branch-focused
pytest suite for the Week 4 AI-Augmented TDD assignment.

> Note: The required instructor starter file was not included with the
> assignment. This implementation reconstructs the stated `/transfer` and
> `/balance` behavior so the TDD and branch-coverage workflow can be completed.

## Setup and testing

```bash
python -m pip install -r requirements.txt
pytest --cov=knight_cash_api --cov-report=html --cov-report=term-missing --cov-branch
```

Open `htmlcov/index.html` to view the detailed coverage report.

## Optional local server

```bash
uvicorn knight_cash_api:app --reload
```

Interactive API documentation will be available at `http://127.0.0.1:8000/docs`.

