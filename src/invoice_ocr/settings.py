import os
import sys

import google.auth
import logfire
from psycopg_pool import ConnectionPool

GOOGLE_CREDENTIALS, GOOGLE_PROJECT_ID = google.auth.default()

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", default="localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", default="5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", default="invoice_ocr")
POSTGRES_USER = os.environ.get("POSTGRES_USER", default="postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", default="postgres")

LOG_LEVEL = os.environ.get("LOG_LEVEL", default="INFO")

logfire.configure()

try:
    POSTGRES_POOL = ConnectionPool(
        conninfo=f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
        min_size=2,
        max_size=10,
        max_idle=300,
        max_lifetime=300,
    )
    POSTGRES_POOL.wait()
    logfire.info(
        f"PostageSQL Pool is ready: postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
except Exception as error:
    logfire.error(f"PostageSQL Pool is not ready: {error}")
    sys.exit(1)
