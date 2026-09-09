from odoo import fields, models


class TenderOrganization(models.Model):
    _name = "tdc.organization"
    _description = "Organization"
    _rec_name = "partner_id"

    name = fields.Char(
        string="Organization",
        required=True,
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
    )

    address = fields.Text()

    phone = fields.Char()

    email = fields.Char()

    website = fields.Char()

    active = fields.Boolean(default=True)