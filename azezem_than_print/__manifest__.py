{
    'name': 'Azezem Than Print',
    'version': '19.0.1.0.0',
    'summary': 'Than Number / Product / Details form with small label print (1.8in x 0.9in)',
    'description': """
Azezem Than Print
==================
Simple custom module with a form containing:
- Than Number (char)
- Product
- Details (char)

Includes a Print button that generates a small label report
(1.8 inch width x 0.9 inch height) showing:

    Azezem
    Than Number: ____________
    Product: ____________
    Details: ____________
""",
    'category': 'Tools',
    'author': 'Techno Digi Codes',
    'depends': ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'report/than_print_paperformat.xml',
        'report/than_print_report.xml',
        'views/than_print_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
