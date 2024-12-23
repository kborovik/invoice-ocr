"""
Cody Instructions:
- Use Pydantic v2.0.0 and above
"""

import re

from pydantic import BaseModel, Field, field_validator


class Address(BaseModel):
    building_number: str = Field(
        title="Building Number",
        description="Building number",
    )
    street: str = Field(
        title="Street",
        description="Street name",
    )
    city: str = Field(
        title="City",
        description="City name",
    )
    province: str = Field(
        title="Province",
        description="Province name",
    )
    postal_code: str = Field(
        title="Postal Code",
        description="Postal Code",
    )
    country: str = Field(
        title="Country",
        description="Country name",
        default="Canada",
    )


class Company(BaseModel):
    id: str = Field(
        title="Company ID",
        description="Company ID based on the following pattern: 4 uppercase letters followed by 1 digit",
        pattern="^[A-Z]{4}[0-9]{1}$",
    )
    name: str = Field(
        title="Company Name",
        description="Company name",
    )
    address: Address = Field(
        title="Company Address",
        description="Company address",
    )
    phone_number: str = Field(
        title="Phone Number",
        description="Phone number",
    )
    email: str = Field(
        title="Email",
        description="Email address",
    )
    website: str = Field(
        title="Website",
        description="Website URL",
    )

    @field_validator("id")
    def validate_company_id(value: str) -> str:  # noqa: N805
        if not re.match(r"^[A-Z]{4}[0-9]{1}$", value):
            raise ValueError("Company ID must be 4 uppercase letters followed by 1 number")
        return value


class Invoice(BaseModel):
    supplier_name: str = Field(
        title="Supplier Name",
        description="The name of the supplier company organization.",
    )
    supplier_address: Address = Field(
        title="Supplier Address",
        description="The address of the supplier company organization.",
    )
