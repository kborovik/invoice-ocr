"""
Cody Instructions:
- Use Python 3.10+
- Use Pydantic v2.0+
"""

import re
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, field_validator


class Address(BaseModel):
    address_line1: str = Field(
        description="Address Line 1, Required",
    )
    address_line2: str = Field(
        description="Address Line 2, Optional",
    )
    city: str = Field(
        description="City name",
    )
    province: str = Field(
        description="Province name",
    )
    postal_code: str = Field(
        description="Postal Code",
    )
    country: str = Field(
        description="Country name",
        default="Canada",
    )

    @field_validator("postal_code", "country")
    def validate_postal_code(postal_code: str, country: str) -> str:  # noqa: N805
        if country == "Canada" and not re.match(r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$", postal_code):
            raise ValueError("Invalid Canadian postal code")
        return postal_code


class Company(BaseModel):
    company_id: str = Field(
        description="Human readable Company ID, must be 4 uppercase letters followed by 1 number",
        pattern="^[A-Z]{4}[0-9]{1}$",
    )
    company_name: str = Field(
        description="Company name",
    )
    address_billing: Address = Field(
        description="Company billing address",
    )
    address_shipping: Address | None = Field(
        description="Company shipping address",
        default=None,
    )
    phone_number: str = Field(
        description="Phone number",
    )
    email: str = Field(
        description="Email address",
    )
    website: str = Field(
        description="Website URL",
    )

    @field_validator("company_id")
    def validate_company_id(company_id: str) -> str:  # noqa: N805
        if not re.match(r"^[A-Z]{4}[0-9]{1}$", company_id):
            raise ValueError("Company ID must be 4 uppercase letters followed by 1 number")
        return company_id


class InvoiceItem(BaseModel):
    item_sku: str = Field(
        description="Stock Keeping Unit (SKU) number, must be 4 uppercase letters followed by 1 number",
        pattern="^[A-Z]{4}[0-9]{1}$",
    )
    item_info: str = Field(
        description="Item or service short information description",
    )
    quantity: int = Field(
        description="Quantity of items",
    )
    unit_price: float = Field(
        description="Price per unit",
    )


class Invoice(BaseModel):
    invoice_number: str = Field(
        description="Unique invoice identifier",
    )
    issue_date: datetime = Field(
        description="Date when invoice was issued",
        default_factory=lambda: datetime.now(),
    )
    supplier: Company = Field(
        description="The name of the supplier company organization.",
    )
    customer: Company = Field(
        description="The address of the supplier company organization.",
    )
    line_items: list[InvoiceItem] = Field(
        description="List of items or services being billed",
        default_factory=list,
    )
    tax_rate: int = Field(
        description="Tax rate applied to the invoice line_items expressed as a percentage",
        default=13,
    )
    payment_terms: str = Field(
        description="Payment terms statement (e.g. 'Net 30', 'Due upon receipt')",
        default="Net 30",
    )
    due_date: datetime = Field(
        description="Due date for payment",
        default_factory=lambda: datetime.now() + timedelta(days=30),
    )
