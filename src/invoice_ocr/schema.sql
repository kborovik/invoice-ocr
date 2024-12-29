--- PostgreSQL database schema for invoice_ocr
---
--- Corresponds to Python class Address
create table if not exists postal_addresses (
  id serial primary key,
  address_line1 varchar(255) not null,
  address_line2 varchar(255),
  city varchar(255) not null,
  province varchar(255) not null,
  postal_code varchar(20) not null,
  country varchar(255) not null,
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp
);

--- Corresponds to Python class Company
create table if not exists companies (
  id serial primary key,
  company_id char(5) not null unique,
  company_name varchar(255) not null,
  address_billing integer references postal_addresses (id),
  address_shipping integer references postal_addresses (id),
  phone_number varchar(20),
  email varchar(255),
  website varchar(255),
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp
);

--- Corresponds to Python class InvoiceItem
create table if not exists invoice_items (
  id serial primary key,
  item_sku char(5) not null unique,
  item_info varchar(255) not null,
  quantity integer not null,
  unit_price decimal(10, 2) not null,
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp
);

-- Corresponds to Python class Invoice
create table if not exists invoices (
  id serial primary key,
  file_origin varchar(4096) not null,
  file_mime_type varchar(20) not null,
  file_sha256 varchar(64) not null unique,
  file_webp bytea,
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp
);
