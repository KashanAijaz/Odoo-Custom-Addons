# -*- coding: utf-8 -*-
{
    "name": "Pakistan FBR Digital Invoicing ",
    "version": "1.0",
    "category": "Accounting",
    'sequence': 215,
    "summary": "Integrate Odoo invoices with FBR Digital Invoicing APIs to get real-time taxes/validation",

    'website': "https://www.zalinotech.com",
    'author': 'Zalino Tech (Private) Limited',
    'company': 'Zalino Tech',
    'maintainer': 'Zalino Tech',
        "description": """FBR Integration App by Zalino Tech seamlessly connects Odoo ERP with Pakistan’s Federal Board of Revenue (FBR) digital invoicing system.
        It ensures that all sales invoices are validated, synced, and compliant with FBR’s prescribed formats, HS Codes, and reporting requirements.
Key Features
------------

- ✅ Automatic synchronization of Odoo invoices with FBR
- ✅ Real-time response handling from FBR APIs
- ✅ Error and status reporting inside Odoo
- ✅ Secure authentication with FBR APIs
- ✅ Audit logs of all invoices synced with FBR

    """,

    "depends": ['account'],
    "data": [
         "security/ir.model.access.csv",
        "views/res_config_views.xml",
        "views/account_move_view.xml",
        "views/product_template.xml",
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    "installable": True,
    "application": False,
    "auto_install": False,
}
