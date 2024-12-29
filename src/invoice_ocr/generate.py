"""
Cody Instructions:
- Use Pydantic v2.0.0 and above
"""

import json

import logfire
from pydantic_ai import Agent, UserError
from pydantic_ai.settings import ModelSettings

from invoice_ocr import db

from .schema import Company, Invoice, InvoiceItem
from .settings import PYDANTIC_AI_MODEL


def create_company() -> Company:
    try:
        company = Agent(
            model=PYDANTIC_AI_MODEL,
            result_type=Company,
            model_settings=ModelSettings(
                temperature=1.5,
                frequency_penalty=1.0,
                presence_penalty=1.0,
            ),
        )
    except UserError as error:
        logfire.error(error)

    schema = json.dumps(Company.model_json_schema())

    user_prompt = f"Generate creative real life company names and company id. Generate unique creative company ID based on company name. Generate unique Canada addresses. Generate unique email address based on company name. Generate unique website URL based on company name. Use JSON schema: {schema}"

    result = company.run_sync(user_prompt=user_prompt)

    logfire.info(
        f"Generated company {result.data.company_id} - {result.data.company_name}. Total tokens: {result._usage.total_tokens}"
    )

    return result.data


def create_invoice_items(quantity: int = 5) -> list[InvoiceItem]:
    try:
        invoice = Agent(
            model=PYDANTIC_AI_MODEL,
            result_type=list[InvoiceItem],
            model_settings=ModelSettings(
                temperature=1.5,
                frequency_penalty=1.0,
                presence_penalty=1.0,
            ),
        )
    except UserError as error:
        logfire.error(error)

    schema = json.dumps(InvoiceItem.model_json_schema())

    user_prompt = f"Generate {quantity} computer equipment invoice line items. Avoid duplicating item_sku and item_info. Use JSON schema for each invoice line item: {schema}"

    result = invoice.run_sync(user_prompt=user_prompt)

    logfire.info(
        f"Generated {quantity} invoice line items. Total tokens: {result._usage.total_tokens}"
    )

    return result.data


def create_invoice() -> Invoice:
    pass


if __name__ == "__main__":
    # companies = gen_companies(quantity=2)
    # for company in companies:
    #     add_company(company)
    # invoices = gen_invoice(quantity=2)
    # for invoice in invoices:
    #     print(invoice.model_dump(exclude_none=True))
    # invoice_items = create_invoice_items(quantity=10)
    # for invoice_item in invoice_items:
    #     print(invoice_item.model_dump(exclude_none=True))
    #     item_id = db.add_invoice_item(invoice_item)
    #     print(f"Item ID: {item_id}")
    invoice_items = db.get_invoice_items()
    for invoice_item in invoice_items:
        invoice_item_json = json.dumps(invoice_item.model_dump(), indent=2)
        print(invoice_item_json)
