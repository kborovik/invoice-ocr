import os
from typing import cast

import google.auth
from pydantic_ai.models import KnownModelName

GOOGLE_CREDENTIALS, GOOGLE_PROJECT_ID = google.auth.default()

PYDANTIC_AI_MODEL = cast(KnownModelName, os.getenv("PYDANTIC_AI_MODEL", "gemini-2.0-flash-exp"))

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", default="localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", default="5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", default="invoice_ocr")
POSTGRES_USER = os.environ.get("POSTGRES_USER", default="postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", default="postgres")

LOG_LEVEL = os.environ.get("LOG_LEVEL", default="INFO")
LOGFIRE_SERVICE_NAME = os.environ.get("LOGFIRE_SERVICE_NAME", default="invoice-ocr")
