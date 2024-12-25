from importlib.metadata import version

import logfire

from .__main__ import main
from .settings import LOGFIRE_SERVICE_NAME

__all__ = ["invoice_ocr", "main"]
__version__ = version("invoice_ocr")

logfire.configure(
    send_to_logfire="if-token-present",
    service_name=LOGFIRE_SERVICE_NAME,
)
