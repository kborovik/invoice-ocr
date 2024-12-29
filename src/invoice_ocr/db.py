import sys
from typing import TypeVar

import logfire
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .schema import Company, InvoiceItem
from .settings import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)

__ALL__ = ["add_company", "add_invoice_item"]

Serial = TypeVar(name="Serial", bound=int)

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
        f"PostageSQL Pool: postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
except Exception as error:
    logfire.error(f"PostageSQL Pool is not ready: {error}")
    sys.exit(1)


def add_company(company: Company) -> int | None:
    """Add Company object to database."""

    with (
        POSTGRES_POOL.connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
        logfire.span("Add Company to DB"),
    ):
        try:
            query_address = """
                INSERT INTO postal_addresses (address_line1, address_line2, city, province, postal_code, country)
                VALUES (%(address_line1)s, %(address_line2)s, %(city)s, %(province)s, %(postal_code)s, %(country)s)
                RETURNING id;
            """
            address_billing = company.address_billing.model_dump()
            cur.execute(query=query_address, params=address_billing)
            address_billing_id = cur.fetchone()["id"]
        except Exception as error:
            logfire.error(f"Failed to insert billing address: {error}")

        try:
            if company.address_shipping:
                address_shipping = company.address_shipping.model_dump()
                cur.execute(query=query_address, params=address_shipping)
                address_shipping_id = cur.fetchone()["id"]
            else:
                address_shipping_id = None
        except Exception as error:
            logfire.error(f"Failed to insert shipping address: {error}")

        try:
            query_company = """
                INSERT INTO companies (company_id, company_name, address_billing, address_shipping, phone_number, email, website)
                VALUES (%(company_id)s, %(company_name)s, %(address_billing)s, %(address_shipping)s, %(phone_number)s, %(email)s, %(website)s)
                RETURNING id;
            """
            cur.execute(
                query=query_company,
                params={
                    "company_id": company.company_id,
                    "company_name": company.company_name,
                    "address_billing": address_billing_id,
                    "address_shipping": address_shipping_id,
                    "phone_number": company.phone_number,
                    "email": company.email,
                    "website": company.website,
                },
            )
            company_id: int = cur.fetchone()["id"]
            assert isinstance(company_id, int)

            logfire.info(f"Inserted Company ID: {company.company_id} - {company.company_name}")

            return company_id

        except UniqueViolation:
            logfire.error(
                f"Company ID {company.company_id} - {company.company_name} already exists"
            )
            return None
        except Exception as error:
            logfire.error(f"Failed to insert company: {error}")
            return None


def get_company(company_id: str) -> list[Company]:
    pass


def add_invoice_item(invoice_item: InvoiceItem) -> int | None:
    """Add InvoiceItem object to database.

    Returns:
     - On success SQL invoice_items table primary key (id)
     - On failure None
    """

    with (
        POSTGRES_POOL.connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
        logfire.span("Add Invoice Item to DB"),
    ):
        try:
            query_invoice_item = """
                INSERT INTO invoice_items (item_sku, item_info, quantity, unit_price)
                VALUES (%(item_sku)s, %(item_info)s, %(quantity)s, %(unit_price)s)
                RETURNING id;
            """
            params = invoice_item.model_dump()
            cur.execute(query=query_invoice_item, params=params)
            invoice_item_id: int = cur.fetchone()["id"]
            assert isinstance(invoice_item_id, int)

            logfire.info(
                f"Inserted Invoice Item: {invoice_item.item_sku} - {invoice_item.item_info}"
            )

            return invoice_item_id

        except UniqueViolation:
            logfire.error(f"Invoice Item SKU {invoice_item.item_sku} already exists")
            return None
        except Exception as error:
            logfire.error(f"Failed to insert invoice item: {error}")
            return None


def get_invoice_items(limit: int = 10) -> list[InvoiceItem]:
    """Fetch invoice items from database with specified limit.

    Args:
        limit: Maximum number of invoice items to return

    Returns:
        List of InvoiceItem objects
    """
    with (
        POSTGRES_POOL.connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
        logfire.span("Get Invoice Items from DB"),
    ):
        try:
            query = """
                SELECT item_sku, item_info, quantity, unit_price
                FROM invoice_items
                ORDER BY created_at DESC
                LIMIT %(limit)s;
            """
            cur.execute(query=query, params={"limit": limit})
            results = cur.fetchall()

            invoice_items = [InvoiceItem(**item) for item in results]

            logfire.info(f"Retrieved {len(invoice_items)} invoice items")

            return invoice_items

        except Exception as error:
            logfire.error(f"Failed to fetch invoice items: {error}")
            return []
