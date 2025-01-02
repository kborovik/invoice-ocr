import sys
from typing import TypeVar

import logfire
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .schema import Address, Company, InvoiceItem
from .settings import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)

__ALL__ = ["add_company", "add_invoice_item"]

SqlId = TypeVar(name="SqlId", bound=int)
"""SQL primary key (id)"""

try:
    POSTGRES_POOL = ConnectionPool(
        conninfo=f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
        open=True,
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


def add_company(company: Company) -> SqlId | None:
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

            logfire.info(f"Insert Company ID: {company.company_id} - {company.company_name}")

            return company_id

        except UniqueViolation:
            logfire.error(
                f"Company ID {company.company_id} - {company.company_name} already exists"
            )
            return None
        except Exception as error:
            logfire.error(f"Failed to insert company: {error}")
            return None


def get_company(company_id: str) -> Company | None:
    """Fetch company from database by company_id.

    Args:
        company_id: Company identifier to search for

    Returns:
        Company objects matching the company_id
    """
    with (
        POSTGRES_POOL.connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
        logfire.span("Get Company from DB"),
    ):
        try:
            query = """
                SELECT c.company_id, c.company_name, c.phone_number, c.email, c.website,
                       b.address_line1 as billing_address_line1,
                       b.address_line2 as billing_address_line2,
                       b.city as billing_city,
                       b.province as billing_province,
                       b.postal_code as billing_postal_code,
                       b.country as billing_country,
                       s.address_line1 as shipping_address_line1,
                       s.address_line2 as shipping_address_line2,
                       s.city as shipping_city,
                       s.province as shipping_province,
                       s.postal_code as shipping_postal_code,
                       s.country as shipping_country
                FROM companies c
                LEFT JOIN postal_addresses b ON c.address_billing = b.id
                LEFT JOIN postal_addresses s ON c.address_shipping = s.id
                WHERE c.company_id = %(company_id)s;
            """
            cur.execute(query=query, params={"company_id": company_id})
            results = cur.fetchone()

            company = Company(
                company_id=results["company_id"],
                company_name=results["company_name"],
                phone_number=results["phone_number"],
                email=results["email"],
                website=results["website"],
                address_billing=Address(
                    address_line1=results["billing_address_line1"],
                    address_line2=results["billing_address_line2"],
                    city=results["billing_city"],
                    province=results["billing_province"],
                    postal_code=results["billing_postal_code"],
                    country=results["billing_country"],
                ),
                address_shipping=Address(
                    address_line1=results["shipping_address_line1"],
                    address_line2=results["shipping_address_line2"],
                    city=results["shipping_city"],
                    province=results["shipping_province"],
                    postal_code=results["shipping_postal_code"],
                    country=results["shipping_country"],
                )
                if results["shipping_address_line1"]
                else None,
            )

            logfire.info(f"Retrieved company: {company.company_id} - {company.company_name}")

            return company

        except Exception as error:
            logfire.error(f"Failed to fetch companies: {error}")
            return None


def find_company(query: str) -> list[Company] | list[None]:
    """Search companies by company_id, company_name, phone_number, email, website.

    Args:
        query: Search string to match against multiple company fields

    Returns:
        List of Company objects matching the search criteria
    """
    with (
        POSTGRES_POOL.connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
        logfire.span("Find Companies in DB"),
    ):
        try:
            search = f"%{query}%"
            sql_query = """
                SELECT company_id
                FROM companies
                WHERE company_id ILIKE %(search)s
                   OR company_name ILIKE %(search)s
                   OR phone_number ILIKE %(search)s
                   OR email ILIKE %(search)s
                   OR website ILIKE %(search)s;
            """
            cur.execute(query=sql_query, params={"search": search})
            results = cur.fetchall()

            companies = []
            for result in results:
                try:
                    company = get_company(result["company_id"])
                except Exception as error:
                    logfire.error(f"Failed to fetch company: {error}")
                    continue
                companies.append(company)

            logfire.info(f"Found {len(companies)} companies matching '{query}'")
            return companies

        except Exception as error:
            logfire.error(f"Failed to search companies: {error}")
            return list[None]


def add_invoice_item(invoice_item: InvoiceItem) -> SqlId | None:
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


def get_invoice_items(limit: int = 2) -> list[InvoiceItem]:
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
