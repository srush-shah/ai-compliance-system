"""Demo documents to seed into raw_data for the one-click demo."""

DEMO_DOCUMENTS = [
    {
        "key": "customer_export",
        "file_name": "northwind_customer_export.json",
        "file_type": "json",
        "content": {
            "raw_text": (
                "Customer export with pricing, healthcare, and export controls.\n"
                "Primary contact SSN 123-45-6789.\n"
                "Temporary payment card used: 4111 1111 1111 1111.\n"
                "HIPAA consent statement missing in clinical notes.\n"
                "This file includes export-controlled component details.\n"
                "Pricing confidentiality clause required for Q4 enterprise deal."
            ),
            "file_name": "northwind_customer_export.json",
            "file_type": "json",
            "source": "demo",
            "parsed_json": {
                "account_id": "NW-4582",
                "summary": "Q4 enterprise proposal with pricing confidentiality clause.",
                "billing_notes": "Card on file: 4111 1111 1111 1111.",
                "primary_contact": "Alex Jordan (SSN 123-45-6789).",
                "clinical_notes": "HIPAA data referenced without consent clause.",
                "export_flags": "Contains export-controlled avionics subsystem references.",
            },
        },
    },
    {
        "key": "support_ticket",
        "file_name": "support_ticket.txt",
        "file_type": "text",
        "content": {
            "raw_text": (
                "Support ticket #9921\n"
                "Customer shared SSN 555-23-9144 in chat transcript.\n"
                "Mentions export-controlled hardware shipment to LATAM.\n"
                "Pricing confidentiality clause referenced in negotiation notes."
            ),
            "file_name": "support_ticket.txt",
            "file_type": "text",
            "source": "demo",
        },
    },
]
