{
    'name': 'Portal Stripe Card Fee',
    'version': '19.0.1.0.0',
    'summary': 'Pass Stripe credit card fee to customers in Odoo standard portal',
    'description': """
Adds an acknowledgment checkbox on Odoo's standard payment portal and
applies a fixed 1.5% Stripe card surcharge as a dedicated line item.
Supports paying invoices, training bookings, and product purchases.
""",
    'author': 'INOM',
    'license': 'LGPL-3',
    'category': 'Accounting/Accounting',
    'depends': [
        'account',
        'payment',
        'portal',
        'website_sale',
        'sale_management',
        'event_sale',
    ],
    'data': [
        'views/res_company_views.xml',
        'views/payment_templates.xml',
    ],
    'installable': True,
    'application': False,
}
