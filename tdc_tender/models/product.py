from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    tender_model = fields.Char(
        string="Model"
    )

    tender_make = fields.Char(
        string="Make"
    )

    tender_specification = fields.Html(
        string="Technical Specification",
        
    )

    technical_key_features = fields.Html(
        string="Key Features",
    )

    technical_power_supply = fields.Html(
        string="Power Supply",
    )
    country_of_origin = fields.Many2one(
        'res.country',
        string='Country of Origin'
    )