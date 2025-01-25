"""
This module provides functionality for generating synthetic invoice and company data.

It uses Pydantic models and AI agents to create realistic test data for the invoice OCR system.
Key components:
- Company generation with unique IDs and Canadian addresses
- Invoice generation with line items
- Integration with database to avoid duplicates

Cody Instructions:
- Use Pydantic v2.0.0 and above
"""

import json
from dataclasses import dataclass
from pathlib import Path

import logfire
from jinja2 import Environment, FileSystemLoader
from pydantic_ai import Agent, RunContext, UserError

from invoice_ocr import db

from .db import get_company, get_invoice_items
from .schema import Company, Invoice, InvoiceItem


@dataclass
class CompanyDeps:
    companies: list[tuple[str, str]] = None

    def __post_init__(self):
        companies = db.find_company("")
        self.companies = [(company.company_id, company.company_name) for company in companies]


company_agent = Agent(
    model="claude-3-5-haiku-latest",
    deps_type=CompanyDeps,
    result_type=Company,
    system_prompt=(
        "You are a helpful assistant that generates company information. "
        "Do not use company names or company IDs that are already in the database. "
    ),
)


@company_agent.system_prompt
def company_agent_system_prompt(context: RunContext[CompanyDeps]) -> str:
    companies = context.deps.companies
    return f"List of companies in database: {companies}"


def create_company() -> Company:
    schema = json.dumps(Company.model_json_schema())

    user_prompt = (
        "Generate creative real life company names."
        "Generate unique company ID based on company name. "
        "Generate unique Canada postal billing address. "
        "Generate unique Canada postal shipping address. "
        "Generate unique email address based on company name. "
        "Generate unique website URL based on company name. "
        f"Use JSON schema: {schema} "
    )

    deps = CompanyDeps()

    try:
        result = company_agent.run_sync(user_prompt=user_prompt, deps=deps)
    except UserError as error:
        logfire.error(error)

    logfire.info(
        f"Generated company {result.data.company_id} - {result.data.company_name}. Total tokens: {result._usage.total_tokens}"
    )

    return result.data


@dataclass
class InvoiceItemsDeps:
    invoice_items: list[tuple[str, str]] = None

    def __post_init__(self):
        invoice_items = db.find_invoice_item("")
        self.invoice_items = [
            (invoice_item.item_sku, invoice_item.item_info) for invoice_item in invoice_items
        ]


invoice_agent = Agent(
    model="claude-3-5-haiku-latest",
    deps_type=InvoiceItemsDeps,
    result_type=list[InvoiceItem],
    system_prompt=(
        "You are a helpful assistant that generates invoice line items. "
        "Do not use item_sku or item_info that are already in database. "
    ),
)


@invoice_agent.system_prompt
def invoice_agent_system_prompt(context: RunContext[InvoiceItemsDeps]) -> str:
    invoice_items = context.deps.invoice_items
    return f"List of item_sku and item_info in database: {invoice_items}"


def create_invoice_items(quantity: int = 5) -> list[InvoiceItem]:
    schema = json.dumps(InvoiceItem.model_json_schema())

    user_prompt = (
        f"Generate {quantity} computer equipment invoice line items. "
        "Avoid duplicate item_sku and item_info. "
        f"Use JSON schema for each invoice line item: {schema}"
    )

    deps = InvoiceItemsDeps()

    result = invoice_agent.run_sync(user_prompt=user_prompt, deps=deps)

    logfire.info(
        f"Generated {quantity} invoice line items. Total tokens: {result._usage.total_tokens}"
    )

    return result.data


def create_pdf_invoice(invoice: Invoice) -> None:
    output_dir = Path("data")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    env = Environment(loader=FileSystemLoader("src/invoice_ocr"))
    template = env.get_template("invoice.j2")
    html_content = template.render(
        invoice_number=invoice.invoice_number,
        issue_date=invoice.issue_date.strftime("%Y-%m-%d"),
        due_date=invoice.due_date.strftime("%Y-%m-%d"),
        supplier=invoice.supplier,
        customer=invoice.customer,
        currency=invoice.currency.value,
        line_items=invoice.line_items,
        tax_rate=invoice.tax_rate,
        tax_total=invoice.tax_total_formatted,
        subtotal=invoice.subtotal_formatted,
        total=invoice.total_formatted,
    )

    output_file = output_dir / f"invoice-{invoice.invoice_number}.html"

    output_file.write_text(html_content, encoding="utf-8")


if __name__ == "__main__":
    supplier = get_company(company_id="MHIA5")
    customer = get_company(company_id="SOLT8")
    invoice_items = get_invoice_items(limit=2)

    invoice = Invoice(
        invoice_number="INV-0001",
        supplier=supplier,
        customer=customer,
        line_items=invoice_items,
    )

    create_pdf_invoice(invoice)
