from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_custom_field = fields.Char(string="Custom Field")
    b = fields.Char(string="B")
    total = fields.Char(string="Total")

    d = fields.Float(string="D")
    f = fields.Float(string="F")

    total_sum = fields.Float(
        string="Sum",
        compute="_compute_total_sum",
        store=True,
    )

    @api.depends("d", "f")
    def _compute_total_sum(self):
        for record in self:
            record.total_sum = record.d + record.f

    