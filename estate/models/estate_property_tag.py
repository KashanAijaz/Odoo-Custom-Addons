from odoo import fields, models


class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Real Estate Property Tag"
    color = fields.Integer(string="Color")

    _sql_constraints = [
        (
            "check_name_unique",
            "UNIQUE(name)",
            "A property tag name must be unique.",
        ),
    ]

    name = fields.Char(string="Name", required=True)