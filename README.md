# ml-tech-assessment

## Environment Setup

### Using Conda (Recommended)

1. Install Conda if you haven't already:
   - Download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/distribution)

2. Create and activate a new conda environment:
   ```bash
   conda create -n ml-assessment python=3.12
   conda activate ml-assessment
   ```

## Installing Poetry and Dependencies

1. Install Poetry using pip:
   ```bash
   pip install poetry
   ```

2. Install project dependencies:
   ```bash
   poetry install
   ```

## Environment Variables

1. Create a `.env` file in the root directory of the project
2. Copy the contents of the provided `.env` file into your local `.env` file

## Running Tests

To run the tests, make sure you have:
1. Activated your virtual environment
2. Installed all dependencies using Poetry
3. Created and populated the `.env` file

Then run:
```bash
pytest
```

For more detailed test output:
```bash
pytest -v
```

For test coverage report:
```bash
pytest --cov
```

## Running the API

Start the FastAPI application with:

```bash
poetry run uvicorn app.main:app --reload
```

If Poetry is not installed globally but dependencies are already installed in the local virtual environment, run:

```bash
./.venv/bin/uvicorn app.main:app --reload
```

Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The Gradio frontend is available at:

```text
http://127.0.0.1:8000/ui
```

Analyze one transcript:

```bash
curl -G "http://127.0.0.1:8000/analyses" \
  --data-urlencode "transcript=Discuss the launch plan and assign next steps."
```

Retrieve a stored analysis:

```bash
curl "http://127.0.0.1:8000/analyses/<analysis-id>"
```

Analyze multiple transcripts concurrently:

```bash
curl -X POST "http://127.0.0.1:8000/analyses/batch" \
  -H "Content-Type: application/json" \
  -d '{"transcripts":["Discuss launch risks.","Review onboarding plan."]}'
```

Analysis results are stored in memory, so they reset when the API process restarts.

## OpenAI Adapter Integration Test

The live OpenAI adapter test is skipped by default so local test runs do not require network access or credentials. To run it explicitly:

```bash
RUN_OPENAI_INTEGRATION_TESTS=1 poetry run pytest tests/adapters/test_openai.py
```
