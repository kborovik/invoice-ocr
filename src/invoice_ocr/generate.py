"""
Cody Instructions:
- Use Pydantic v2.0.0 and above
"""

import json
import sys
from logging import basicConfig, getLogger

import logfire
from pydantic_ai import Agent, UserError
from pydantic_ai.settings import ModelSettings

from .schema import CompanyName
from .settings import LOGFIRE_SERVICE_NAME, PYDANTIC_AI_MODEL

logfire.configure(send_to_logfire="if-token-present", service_name=LOGFIRE_SERVICE_NAME)
logfire.instrument_pydantic()
basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = getLogger(__name__)


def generate_company_name(number: int = 2) -> list[CompanyName]:
    try:
        company_names = Agent(
            model=PYDANTIC_AI_MODEL,
            result_type=list[CompanyName],
            model_settings=ModelSettings(
                temperature=1.5,
                frequency_penalty=1.0,
                presence_penalty=1.0,
            ),
        )
    except UserError as error:
        logger.error(error)
        sys.exit(1)

    result = company_names.run_sync(
        f"Generate {number} creative (real life) company names and company id. Generate unique creative company ID based on company name. Schema: {CompanyName.model_json_schema()}",
    )

    return result.data


if __name__ == "__main__":
    results = generate_company_name(number=3)
    print(json.dumps([result.model_dump() for result in results], indent=2))
