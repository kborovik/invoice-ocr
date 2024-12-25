import sys

import logfire
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .schema import Company
from .settings import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)

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
        f"PostageSQL Pool is ready: postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
except Exception as error:
    logfire.error(f"PostageSQL Pool is not ready: {error}")
    sys.exit(1)


def put_company(company: Company) -> bool:
    """Put Company object into database."""
    status = False

    with (
        POSTGRES_POOL.connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
        logfire.span("Insert Company"),
    ):
        try:
            query_insert_address = """INSERT INTO postal_addresses (address_line1, address_line2, city, province, postal_code, country)
            VALUES (%(address_line1)s, %(address_line2)s, %(city)s, %(province)s, %(postal_code)s, %(country)s)
            RETURNING id
            """
            address_billing = company.address_billing.model_dump()

            cur.execute(
                query=query_insert_address,
                params=address_billing,
            )
            address_billing_id = cur.fetchone()["id"]
        except Exception as error:
            logfire.error(f"Failed to insert billing address: {error}")

        try:
            if company.address_shipping:
                address_shipping = company.address_shipping.model_dump()
                cur.execute(
                    query=query_insert_address,
                    params=address_shipping,
                )
                address_shipping_id = cur.fetchone()["id"]
            else:
                address_shipping_id = None
        except Exception as error:
            logfire.error(f"Failed to insert shipping address: {error}")

        try:
            query_insert_company = """INSERT INTO companies (company_id, company_name, address_billing, address_shipping, phone_number, email, website)
            VALUES (%(company_id)s, %(company_name)s, %(address_billing)s, %(address_shipping)s, %(phone_number)s, %(email)s, %(website)s)
            """
            cur.execute(
                query=query_insert_company,
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
            status = True

        except UniqueViolation:
            logfire.error(f"Company ID {company.company_id} already exists")
        except Exception as error:
            logfire.error(f"Failed to insert company: {error}")

    return status
