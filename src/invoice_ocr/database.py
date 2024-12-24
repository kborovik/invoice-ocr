import sys
from logging import getLogger

from psycopg_pool import ConnectionPool

from .settings import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)

logger = getLogger(__name__)

try:
    POSTGRES_POOL = ConnectionPool(
        conninfo=f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
        min_size=2,
        max_size=10,
        max_idle=300,
        max_lifetime=300,
    )
    POSTGRES_POOL.wait()
    logger.success(
        f"PostageSQL Pool is ready: postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
except Exception as error:
    logger.error(f"PostageSQL Pool is not ready: {error}")
    sys.exit(1)
