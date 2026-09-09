from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    manufacturer_name = fields.Char(
        string="Manufacturer Name"
    )

    warranty_period = fields.Integer(
        string="Warranty (Months)"
    )

    is_returnable = fields.Boolean(
        string="Returnable"
    )

    launch_date = fields.Date(
        string="Launch Date"
    )
    default_code = fields.Char(
        string = "Code"
    )