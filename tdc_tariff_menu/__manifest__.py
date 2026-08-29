# -*- coding: utf-8 -*-
{
    'name': 'TDC Tariff Menu',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'GD based Tariff / Duty calculation sheet pulling HS Code, '
               'CD, ACD, RD and taxes from the selected product',
    'description': """
TDC Tariff Menu
===============
Create GD (Goods Declaration) based tariff sheets.

Header
------
* GD Number
* GD Date
* Currency Import
* GD Payment Exchange Rate
* Insurance % (on CFR Value)
* Landing Charges % (on CFR Value)

Product Lines
-------------
For every product added to a tariff line, the following is pulled
automatically from the product:
* HS Code
* Customs Duty (CD)
* Additional Customs Duty (ACD)
* Regulatory Duty (RD)
* Sales Tax / Advance Sales Tax / Income Tax (from the product's taxes)

Note
----
This module adds HS Code / CD / ACD / RD fields directly on the Product
(Inventory > Products > Tariff Info tab) and a "TDC Tax Category" field on
Taxes (Accounting > Configuration > Taxes) so that Sales Tax / Advance
Sales Tax / Income Tax can be identified automatically. If you already
have a dedicated HS Code app/model, let us know its technical module
name and these fields can be linked to it instead of duplicated here.
""",
    'author': 'TDC',
    'website': '',
    'depends': ['product', 'account' , 'hs_code_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/account_tax_views.xml',
        'views/tdc_tariff_menu_views.xml',
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
