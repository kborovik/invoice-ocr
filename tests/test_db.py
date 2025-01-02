import pytest

from invoice_ocr.db import (
    POSTGRES_POOL,
    add_company,
    add_invoice_item,
    find_company,
    find_invoice_item,
    get_company,
    get_invoice_item,
    get_invoice_items,
)
from invoice_ocr.schema import Address, Company, InvoiceItem

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
    address_shipping=None,
)

INVOICE_ITEM = InvoiceItem(
    item_sku="ABCD1",
    item_info="Widget Description",
    quantity=10,
    unit_price=10.0,
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
    assert isinstance(companies, list)
    assert isinstance(companies[0], Company)
    assert companies[0].company_id == COMPANY.company_id
    assert companies[0].company_name == COMPANY.company_name


@pytest.mark.db
def test_add_invoice_item():
    invoice_item_id = add_invoice_item(INVOICE_ITEM)
    assert invoice_item_id is not None
    assert isinstance(invoice_item_id, int)


@pytest.mark.db
def test_get_invoice_item():
    invoice_item = get_invoice_item(INVOICE_ITEM.item_sku)
    assert invoice_item is not None
    assert isinstance(invoice_item, InvoiceItem)
    assert invoice_item.item_sku == INVOICE_ITEM.item_sku
    assert invoice_item.item_info == INVOICE_ITEM.item_info
    assert invoice_item.quantity == INVOICE_ITEM.quantity
    assert invoice_item.unit_price == INVOICE_ITEM.unit_price


@pytest.mark.db
def test_get_invoice_items():
    invoice_items = get_invoice_items(limit=1)
    assert invoice_items is not None
    assert isinstance(invoice_items, list)
    assert isinstance(invoice_items[0], InvoiceItem)


@pytest.mark.db
def test_find_invoice_item():
    invoice_items = find_invoice_item(INVOICE_ITEM.item_sku)
    assert invoice_items is not None
    assert isinstance(invoice_items, list)
    assert isinstance(invoice_items[0], InvoiceItem)
    assert invoice_items[0].item_sku == INVOICE_ITEM.item_sku
    assert invoice_items[0].item_info == INVOICE_ITEM.item_info
    assert invoice_items[0].quantity == INVOICE_ITEM.quantity
    assert invoice_items[0].unit_price == INVOICE_ITEM.unit_price

    invoice_items = find_invoice_item("")
    assert invoice_items is not None
    assert isinstance(invoice_items, list)
    assert isinstance(invoice_items[0], InvoiceItem)
    assert invoice_items[0].item_sku == INVOICE_ITEM.item_sku
    assert invoice_items[0].item_info == INVOICE_ITEM.item_info
    assert invoice_items[0].quantity == INVOICE_ITEM.quantity
    assert invoice_items[0].unit_price == INVOICE_ITEM.unit_price


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
        if COMPANY.address_shipping:
            cur.execute(
                "DELETE FROM postal_addresses WHERE address_line1 = %s AND city = %s AND postal_code = %s",
                (
                    COMPANY.address_shipping.address_line1,
                    COMPANY.address_shipping.city,
                    COMPANY.address_shipping.postal_code,
                ),
            )
        cur.execute("DELETE FROM invoice_items WHERE item_sku = %s", (INVOICE_ITEM.item_sku,))
