{
    'name': 'Tdc Purchase Customization',
    'version': '19.0.1.0.0',
    'summary': 'Local / Import Purchase Order type with extended Import approval-payment-shipment workflow',
    'description': """
Purchase Order par ek naya field "Purchase Order Type" (Local / Import) add karta hai,
Vendor field se pehle.

- Local Purchase: standard Odoo flow, kuch change nahi (RFQ -> RFQ Sent -> To Approve -> Purchase Order).
- Import Purchase: extended flow:
    Proforma INV -> RFQ Sent -> To Approve -> Purchase Order -> Payment Under Process ->
    Payment Completed -> Order Confirmation -> Shipment Pickup

Order Confirmation aur Shipment Pickup states par notebook mein naye tabs aate hain jinme
extra fields, Note aur Attachment Lines hote hain.
    """,
    'category': 'Purchases',
    'author': 'Custom',
    'depends': ['purchase', 'purchase_stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
