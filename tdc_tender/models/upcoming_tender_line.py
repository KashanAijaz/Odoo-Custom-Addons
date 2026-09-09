from odoo import api, fields, models
from odoo.exceptions import ValidationError

class UpcomingTenderLine(models.Model):
    _name = "tdc.upcoming.tender.line"
    _description = "Upcoming Tender Products"

    tender_id = fields.Many2one(
        "tdc.upcoming.tender",
        
    )

    sequence = fields.Integer("S#")

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
    )

    model = fields.Char(
        related="product_id.product_tmpl_id.tender_model",
        string="Model",
        store=True,
    )

    qty = fields.Float(
        default=1,
    )

    uom_id = fields.Many2one(
        related="product_id.uom_id",
        string="UoM",
        store=True,
    )

    remarks = fields.Char()