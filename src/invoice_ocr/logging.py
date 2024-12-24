from logging import Logger, basicConfig, getLogger

import logfire

from .settings import LOGFIRE_SERVICE_NAME


def setup_logging() -> Logger:
    logfire.configure(send_to_logfire="if-token-present", service_name=LOGFIRE_SERVICE_NAME)
    logfire.instrument_pydantic()
    basicConfig(handlers=[logfire.LogfireLoggingHandler()])
    logger = getLogger(__name__)
    return logger
