from odoo import fields, models


class TDCPaymentMethod(models.Model):
    _name = "tdc.payment.method"
    _description = "Tender Payment Method"
    _order = "sequence, name"

    name = fields.Char(
        string="Payment Method",
        required=True,
    )

    sequence = fields.Integer(
        default=10,
    )

    active = fields.Boolean(
        default=True,
    )