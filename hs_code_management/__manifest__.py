# -*- coding: utf-8 -*-
{
    'name': 'Product Customization and HS Code',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Manage HS Codes and show them on Products, Sales, Purchases, Invoices and Bills',
    'description': """
HS Code Management
===================
This module adds:
- A new master data model "HS Code" (Menu: Purchase > Configuration > Products > HS Code)
  with fields: HS Code, Description, CD % (Custom Duty %)
- An "HS Code" field on the Product form
- An editable "HS Code" field/column on:
    * Sales Order lines
    * Purchase Order lines
    * Customer Invoice lines
    * Vendor Bill lines
  The field is automatically filled from the product's HS Code when a product is
  selected, but can still be changed manually on each line.
""",
    'author': 'Custom Development',
    'depends': ['sale_management', 'purchase', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/hs_code_views.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        "views/res_partner_views.xml",
        "views/product_template_views.xml",
        "views/stock_picking_view.xml"
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
