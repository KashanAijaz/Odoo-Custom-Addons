{
    'name': 'TDC Quotation - Custom Sequence (QT/SO)',
    'version': '19.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Sale Order ka naam state k mutabiq QT (Quotation) ya SO (Sale Order) se start hota hai',
    'description': """
TDC Quotation Custom Sequence
==============================
Yeh module sale.order (model) k "name" field ko customize karta hai:

- Agar state = 'sale' (Sales Order)      -> Naam "SO0001", "SO0002" ... se start hoga
- Agar state = 'draft' (Quotation)        -> Naam "QT0001", "QT0002" ... se start hoga
- Agar state = 'sent' (Quotation Sent)    -> Naam "QT0001", "QT0002" ... se start hoga
- Agar state = 'cancel' (Cancelled)       -> Naam "QT0001", "QT0002" ... se start hoga

Jab Quotation confirm hoke Sale Order banti hai to naam automatically SO series
se replace ho jata hai, aur agar wapis cancel/draft ho to QT series se.
    """,
    'author': 'TDC',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['sale'],
    'data': [
        'data/ir_sequence_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
