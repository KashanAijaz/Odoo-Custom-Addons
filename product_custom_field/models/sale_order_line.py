from odoo import models, fields

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_code = fields.Char(
        related="product_id.default_code",
        string="Code",
        store=True,
    )