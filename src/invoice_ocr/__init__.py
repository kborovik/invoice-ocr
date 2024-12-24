from importlib.metadata import version

from .__main__ import main
from .logging import setup_logging

__all__ = ["invoice_ocr", "main"]
__version__ = version("invoice_ocr")

logger = setup_logging()
