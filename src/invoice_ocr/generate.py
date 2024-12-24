"""
Cody Instructions:
- Use Pydantic v2.0.0 and above
"""

import json
import sys
from logging import getLogger

import logfire
from pydantic_ai import Agent, UserError
from pydantic_ai.settings import ModelSettings

from .schema import Company
from .settings import PYDANTIC_AI_MODEL

logger = getLogger(__name__)


def gen_company(quantity: int = 2) -> list[Company]:
    try:
        company_names = Agent(
            model=PYDANTIC_AI_MODEL,
            result_type=list[Company],
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
        f"Generate {quantity} creative (real life) company names and company id. Generate unique creative company ID based on company name. Generate unique Canada addresses. Generate unique email address based on company name. Generate unique website URL based on company name. Schema: {Company.model_json_schema()}",
    )

    logfire.info(f"Tokens: {result._usage}")

    return result.data


if __name__ == "__main__":
    test_companies = gen_company(quantity=2)
    print(json.dumps([item.model_dump() for item in test_companies], indent=2))
