"""
Cody Instructions:
- Use Pydantic v2.0.0 and above
"""

import re

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
        description="Human readable Company ID",
        pattern="^[A-Z]{4}[0-9]{1}$",
    )
    company_name: str = Field(
        description="Company name",
    )
    address_billing: Address = Field(
        description="Company billing address",
    )
    address_shipping: Address = Field(
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


class Invoice(BaseModel):
    supplier_name: str = Field(
        title="Supplier Name",
        description="The name of the supplier company organization.",
    )
    supplier_address: Address = Field(
        title="Supplier Address",
        description="The address of the supplier company organization.",
    )
