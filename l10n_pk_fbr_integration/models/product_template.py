from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    hs_code = fields.Char(
        string="HS Code",
        help="Harmonized System Code for customs and taxation purposes."
    )

    hs_unit_measure = fields.Char(
        string="HS Unit of Measure",
        help="Harmonized System Unit of Measure for customs and taxation purposes."
    )

