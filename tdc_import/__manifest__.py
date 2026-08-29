# -*- coding: utf-8 -*-
{
    'name': 'TDC Import - GD Tariff Management',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'GD / Import Tariff calculation using HS Code based duties (CD, RD, ACD) and taxes (ST, AST, IT)',
    'description': """
TDC Import - GD Tariff Management
==================================
This module adds an "Import" menu with a "Tariff" sub-menu allowing to
record Goods Declaration (GD) based import tariff calculations:

* GD No., GD Date, Vendor
* Currency of Import (EUR, USD, ...) and GD Payment Exchange Rate
* Insurance % and Landing Charges % (applied on CFR value)
* Tariff lines: select the Item -> HS Code, CD %, RD %, ACD % are
  fetched automatically from the product's HS Code (hs_code_management
  module). Sales Tax (ST), Additional Sales Tax (AST) and Income Tax
  (IT) percentages are fetched from account.tax records.
* Automatic calculation of Assessed Value (foreign currency & PKR),
  duties (CD/RD/ACD) and taxes (ST/AST/IT) in PKR, and Total Sum
  Payable (PKR).
* Excel export wizard and a printable GD Tariff report.
""",
    'author': 'TDC',
    'license': 'LGPL-3',
    'depends': ['base', 'product', 'account', 'uom', 'hs_code_management', 'tdc_product_customization'],
    'data': [
        'security/ir.model.access.csv',
        'data/tdc_master_import_sequence.xml',
        'data/tdc_import_charge_products.xml',
        'views/tdc_import_master_data_views.xml',
        'views/tdc_master_import_views.xml',
        'views/tariff_views.xml',
        'views/tariff_report_views.xml',
        'reports/tariff_report_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
