"""
Cody Instructions:
- Use Pydantic v2.0.0 and above
"""

import sys

import logfire
from pydantic_ai import Agent, UserError
from pydantic_ai.settings import ModelSettings

from .database import add_company
from .schema import Company
from .settings import PYDANTIC_AI_MODEL


def gen_companies(quantity: int = 2) -> list[Company]:
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
        logfire.error(error)
        sys.exit(1)

    result = company_names.run_sync(
        f"Generate {quantity} creative (real life) company names and company id. Generate unique creative company ID based on company name. Generate unique Canada addresses. Generate unique email address based on company name. Generate unique website URL based on company name. Schema: {Company.model_json_schema()}",
    )

    logfire.info(
        f"Generated {len(result.data)} companies. Total tokens: {result._usage.total_tokens}"
    )

    return result.data


def store_companies(companies: list[Company]) -> bool:
    pass


if __name__ == "__main__":
    companies = gen_companies(quantity=2)

    for company in companies:
        add_company(company)
