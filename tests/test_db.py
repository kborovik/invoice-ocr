import pytest

from invoice_ocr.db import POSTGRES_POOL, add_company, find_company, get_company
from invoice_ocr.schema import Address, Company

COMPANY = Company(
    company_id="TEST1",
    company_name="Test Company",
    phone_number="+1-555-123-4567",
    email="contact@testcompany.com",
    website="https://testcompany.com",
    address_billing=Address(
        address_line1="789 Elm St",
        address_line2="Apt 5B",
        city="Toronto",
        province="ON",
        postal_code="M5A 1A1",
        country="Canada",
    ),
    address_shipping=Address(
        address_line1="456 Warehouse Ave",
        address_line2="Unit 200",
        city="Toronto",
        province="ON",
        postal_code="M5V 2B2",
        country="Canada",
    ),
)


@pytest.mark.db
def test_add_company():
    company_id = add_company(COMPANY)
    assert company_id is not None
    assert isinstance(company_id, int)


@pytest.mark.db
def test_get_company():
    company = get_company(COMPANY.company_id)
    assert company is not None
    assert isinstance(company, Company)
    assert company.company_id == COMPANY.company_id
    assert company.company_name == COMPANY.company_name
    assert company.phone_number == COMPANY.phone_number
    assert company.email == COMPANY.email
    assert company.website == COMPANY.website
    assert company.address_billing == COMPANY.address_billing
    assert company.address_shipping == COMPANY.address_shipping


@pytest.mark.db
def test_find_company():
    companies = find_company(COMPANY.company_id)
    assert companies is not None
    assert len(companies) >= 1
    assert companies[0].company_id == COMPANY.company_id
    assert companies[0].company_name == COMPANY.company_name


@pytest.fixture(scope="session", autouse=True)
def cleanup_database():
    yield
    with (
        POSTGRES_POOL.connection() as conn,
        conn.cursor() as cur,
    ):
        cur.execute("DELETE FROM companies WHERE company_id = %s", (COMPANY.company_id,))
        cur.execute(
            "DELETE FROM postal_addresses WHERE address_line1 = %s AND city = %s AND postal_code = %s",
            (
                COMPANY.address_billing.address_line1,
                COMPANY.address_billing.city,
                COMPANY.address_billing.postal_code,
            ),
        )
        cur.execute(
            "DELETE FROM postal_addresses WHERE address_line1 = %s AND city = %s AND postal_code = %s",
            (
                COMPANY.address_shipping.address_line1,
                COMPANY.address_shipping.city,
                COMPANY.address_shipping.postal_code,
            ),
        )