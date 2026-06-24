FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY policypulse_api ./policypulse_api
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "policypulse_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

