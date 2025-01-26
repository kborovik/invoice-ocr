import argparse
from pathlib import Path
from random import randint

import logfire

from . import db
from . import generate as gen
from .schema import Invoice


def main() -> None:
    parser = argparse.ArgumentParser(description="Invoice OCR CLI tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate invoices command
    gen_parser = subparsers.add_parser("invoice", help="Generate synthetic invoice PDFs")
    gen_parser.add_argument(
        "-n",
        "--num-invoices",
        type=int,
        default=1,
        help="Number of invoices to generate (default: 1)",
    )
    gen_parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Output directory for PDF files (default: ./data)",
    )

    # Create companies command
    company_parser = subparsers.add_parser("company", help="Create synthetic companies")
    company_parser.add_argument(
        "-n",
        "--num-companies",
        type=int,
        default=1,
        help="Number of companies to create (default: 1)",
    )

    # Create invoice items command
    items_parser = subparsers.add_parser("invoice-item", help="Create synthetic invoice items")
    items_parser.add_argument(
        "-n",
        "--num-items",
        type=int,
        default=5,
        help="Number of invoice items to create (default: 5)",
    )

    args = parser.parse_args()

    if args.command == "invoice":
        # Create output directory if it doesn't exist
        args.output_dir.mkdir(parents=True, exist_ok=True)

        for i in range(args.num_invoices):
            companies = db.get_random_companies(limit=2)
            invoice_items = db.get_random_invoice_items(limit=randint(1, 10))

            invoice = Invoice(
                invoice_number=f"INV-{randint(1000, 9999)}",
                supplier=companies[0],
                customer=companies[1],
                line_items=invoice_items,
            )

            pdf_bytes = gen.create_pdf_invoice(invoice)
            pdf_path = args.output_dir / f"{invoice.invoice_number}.pdf"
            pdf_path.write_bytes(pdf_bytes)

            logfire.info(f"Generated invoice PDF: {pdf_path}")

        logfire.info(f"Successfully generated {args.num_invoices} invoice(s)")

    elif args.command == "company":
        for i in range(args.num_companies):
            company = gen.create_company()
            company_id = db.add_company(company=company)
            if not company_id:
                logfire.error(f"Failed to create company {i + 1}/{args.num_companies}")

    elif args.command == "invoice-item":
        invoice_items = gen.create_invoice_items(quantity=args.num_items)
        for invoice_item in invoice_items:
            item_id = db.add_invoice_item(invoice_item=invoice_item)
            if not item_id:
                logfire.error(f"Failed to create invoice item {args.num_items}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
