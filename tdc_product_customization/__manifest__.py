# -*- coding: utf-8 -*-
{
    'name': "TDC Product Customization",
    'summary': "Adds sourcing, pricing and packing/weight fields to Product Templates.",
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

No core Odoo files are modified. All changes are additive, delivered through
model inheritance (_inherit) and view inheritance (XPath).
    """,
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'author': "TDC",
    'license': 'LGPL-3',

    # 'product' is the only functional dependency: it defines product.template
    # and the product.product_template_only_form_view we inherit from.
    # 'uom' is pulled in automatically as a dependency of 'product', but we do
    # not need to depend on it directly since we don't touch UoM logic.
    'depends': [
        'product',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
