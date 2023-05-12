FROM python:3.9

WORKDIR /app
COPY setup.py setup.cfg pyproject.toml ./
COPY src/ src/

RUN pip install .[dev]

COPY tests/ tests/
