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
    """Adds a new company to the database with its billing and optional shipping address.

    This function inserts a company's details into the database, including:
    - Inserting billing address into postal_addresses table
    - Optionally inserting shipping address into postal_addresses table
    - Inserting company details into companies table with address references

    Args:
        company (Company): A Company object containing company details including:
            - company_id (str): Unique identifier for the company
            - company_name (str): Name of the company
            - address_billing (Address): Billing address details
            - address_shipping (Address, optional): Shipping address details
            - phone_number (str): Company phone number
            - email (str): Company email address
            - website (str): Company website URL

    Returns:
        SqlId | None: The database ID of the newly inserted company if successful,
        None if insertion fails due to:
        - Duplicate company ID
        - Database insertion errors

    Raises:
        UniqueViolation: If a company with the same company_id already exists
        Exception: For any other database-related errors during insertion
    """

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
            return None

        try:
            if company.address_shipping:
                address_shipping = company.address_shipping.model_dump()
                cur.execute(query=query_address, params=address_shipping)
                address_shipping_id = cur.fetchone()["id"]
            else:
                address_shipping_id = None
        except Exception as error:
            logfire.error(f"Failed to insert shipping address: {error}")
            return None

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
    """Retrieves a company's details from the database by its unique company ID.

    This function queries the database to fetch comprehensive company information,
    including basic company details and both billing and shipping addresses.
    It performs a left join with postal addresses to retrieve address information.

    Args:
        company_id (str): The unique identifier of the company to retrieve.

    Returns:
        Company | None: A Company object with all retrieved details if found,
        or None if no company is found or an error occurs during retrieval.

    Raises:
        Exception: Logs and returns None if any database or query-related error occurs.
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

            if results is None:
                logfire.info(f"No company found with ID: {company_id}")
                return None

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
    """Searches for companies in the database based on a search query.

    Searches across company_id, company_name, phone_number, email, and website
    using case-insensitive partial matching.

    Args:
        query: A string to search for in company details.

    Returns:
        A list of Company objects matching the search query, or an empty list
        if no companies are found or an error occurs.
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
            return []


def add_invoice_item(invoice_item: InvoiceItem) -> SqlId | None:
    """Adds a new invoice item to the database.

    Args:
        invoice_item: The InvoiceItem object to be inserted into the database.

    Returns:
        The ID of the newly inserted invoice item if successful, None otherwise.

    Raises:
        UniqueViolation: If an invoice item with the same SKU already exists.
        Exception: For any other database insertion errors.
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


def get_invoice_item(item_sku: str) -> InvoiceItem | None:
    """Retrieves a single invoice item from the database by its SKU.

    This function queries the database to fetch an invoice item's details using
    its unique SKU (Stock Keeping Unit). It returns comprehensive information
    about the item including its description, quantity, and unit price.

    Args:
        item_sku (str): The unique Stock Keeping Unit identifier for the invoice item.

    Returns:
        InvoiceItem | None: An InvoiceItem object containing all item details if found,
        or None if no item matches the provided SKU or if an error occurs.

    Raises:
        Exception: Logs the error and returns None if any database or query-related
            error occurs during retrieval.
    """
    with (
        POSTGRES_POOL.connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
        logfire.span("Get Invoice Item from DB"),
    ):
        try:
            query = """
                SELECT item_sku, item_info, quantity, unit_price
                FROM invoice_items 
                WHERE item_sku = %(item_sku)s;
            """
            cur.execute(query=query, params={"item_sku": item_sku})
            result = cur.fetchone()

            if result is None:
                return None

            invoice_item = InvoiceItem(**result)

            logfire.info(
                f"Retrieved invoice item: {invoice_item.item_sku} - {invoice_item.item_info}"
            )

            return invoice_item

        except Exception as error:
            logfire.error(f"Failed to fetch invoice item: {error}")
            return None


def get_invoice_items(limit: int = 2) -> list[InvoiceItem]:
    """Retrieves a list of the most recent invoice items from the database.

    This function queries the database to fetch multiple invoice items, ordered by
    their creation date in descending order. The number of items returned is
    controlled by the limit parameter.

    Args:
        limit (int, optional): Maximum number of invoice items to retrieve.
            Defaults to 2.

    Returns:
        list[InvoiceItem]: A list of InvoiceItem objects containing the most
            recent invoice items. Returns an empty list if no items are found
            or if an error occurs.

    Raises:
        Exception: Logs the error and returns an empty list if any database
            or query-related error occurs during retrieval.
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


def find_invoice_item(query: str) -> list[InvoiceItem] | list[None]:
    """Searches for invoice items in the database based on a search query.

    This function performs a case-insensitive search across item_sku and item_info
    fields in the invoice_items table. Results are ordered by creation date in
    descending order.

    Args:
        query (str): A string to search for in invoice item details. The search is
            performed using partial matching (contains) on both SKU and item info.

    Returns:
        list[InvoiceItem] | list[None]: A list of InvoiceItem objects matching the
            search query, ordered by creation date (newest first). Returns an empty
            list if no items are found or if an error occurs during the search.

    Raises:
        Exception: Logs the error and returns an empty list if any database or
            query-related error occurs during the search operation.
    """
    with (
        POSTGRES_POOL.connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
        logfire.span("Find Invoice Items in DB"),
    ):
        try:
            search = f"%{query}%"
            sql_query = """
                SELECT item_sku, item_info, quantity, unit_price 
                FROM invoice_items
                WHERE item_sku ILIKE %(search)s
                   OR item_info ILIKE %(search)s
                ORDER BY created_at DESC;
            """
            cur.execute(query=sql_query, params={"search": search})
            results = cur.fetchall()

            invoice_items = [InvoiceItem(**item) for item in results]

            logfire.info(f"Found {len(invoice_items)} invoice items matching '{query}'")
            return invoice_items

        except Exception as error:
            logfire.error(f"Failed to search invoice items: {error}")
            return []
