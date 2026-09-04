# -*- coding: utf-8 -*-
{
    'name': "TDC Product Customization",
    'summary': "Adds sourcing, pricing and packing/weight fields to Product Templates, plus Child Product wizards for Sale/Purchase orders.",
    'description': """
TDC Product Customization
==========================
This module extends the standard Product Template (product.template) with:

* Source Information: Purchase Source (Local Purchase / Import Purchase).
* Pricing: EXW Origin List Price, EXW Origin Net Transfer Price (with their own
  currencies), Normal Selling Rate and Competitive Selling Rate.
* Packing Details: Net Weight, Gross Weight, physical dimensions
  (Length / Width / Height), a computed Volumetric Weight and a computed
  Chargeable Weight (CW Weight).
* Child Products: a Child Products tab on the Product Template, plus wizards
  to pull child products directly into Sale Order and Purchase Order lines.

No core Odoo files are modified. All changes are additive, delivered through
model inheritance (_inherit) and view inheritance (XPath).
    """,
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'author': "TDC",
    'license': 'LGPL-3',

    # 'product' defines product.template and the base form view we inherit from.
    # 'sale' and 'purchase' are required for the child product wizards on
    # Sale Order and Purchase Order lines.
    'depends': [
        'product',
        'sale',
        'purchase',
    ],

    'data': [
        'security/ir.model.access.csv',

        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',

        'wizard/sale_child_product_wizard_views.xml',
        'wizard/purchase_child_product_wizard_views.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}