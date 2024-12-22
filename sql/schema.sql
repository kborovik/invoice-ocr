--- PostgreSQL database schema for invoice_ocr
---
-- ocr_invoices table corresponds to OcrInvoice Python class
create table if not exists invoices (
  invoice_id serial primary key,
  file_origin varchar(4096) not null,
  file_mime_type varchar(20) not null,
  file_sha256 varchar(64) not null unique,
  file_webp bytea,
  created_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp
);
