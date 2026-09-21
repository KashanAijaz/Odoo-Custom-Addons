{
    'name': 'TDC UoM Calculation',
    'version': '19.0.1.0.0',
    'summary': 'Ft/Kg quantity calculation on Sale & Purchase Order lines based on product Weight Kg./Ft.',
    'description': """
TDC UoM Calculation
====================
- Adds "Weight Kg./Ft." field on Product (product.product), shown after Category.
- On Sale Order and Purchase Order lines:
    * Quantity and Unit are readonly only when the line's Unit is Ft or Kg.
    * Two checkboxes, "In Ft" and "In Kg", appear next to Unit (mutually
      exclusive), only shown when Unit is Ft/Kg.
    * Two new fields "Qty in Ft." and "Qty in Kg." next to Unit; whichever
      side is NOT checked is readonly and auto-shows the converted value.
    * Conversion factor is pulled from the product's own "Weight Kg./Ft."
      value, not a fixed constant.
    """,
    'category': 'Purchases',
    'author': 'Techno Digi Codes',
    'depends': ['purchase', 'sale', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
        'views/product_views.xml',
        'views/purchase_reference_wizard_views.xml',
        'reports/purchase_reference_report.xml',
        'reports/purchase_reference_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}