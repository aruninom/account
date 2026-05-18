{
    "name": "OEHealth Core",
    "summary": "Enterprise Healthcare Core for Hospitals & Clinics",
    "description": """
OEHealth Core
=============
A production-grade healthcare foundation module for Odoo 19 with scalable
architecture spanning patient management, appointments, clinical records,
surgery, pharmacy, operations, billing, insurance readiness, communication,
analytics, and ERP integration touchpoints.
""",
    "version": "19.0.1.0.0",
    "author": "OEHealth",
    "website": "https://example.com",
    "license": "LGPL-3",
    "category": "Healthcare",
    "depends": ["base", "mail", "contacts", "calendar", "web"],
    "data": [
        "security/oehealth_security.xml",
        "security/ir.model.access.csv",
        "data/oehealth_sequences.xml",
        "views/oehealth_menus.xml",
        "views/oehealth_patient_views.xml",
        "views/oehealth_appointment_views.xml",
        "views/oehealth_clinical_views.xml",
        "views/oehealth_operation_views.xml",
        "views/oehealth_finance_views.xml",
        "views/oehealth_dashboard_views.xml",
    ],
    "application": True,
    "installable": True,
}
