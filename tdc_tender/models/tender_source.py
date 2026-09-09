from odoo import fields, models


class TDCTenderSource(models.Model):
    _name = "tdc.tender.source"
    _description = "Tender Source"
    _order = "sequence, name"

    sequence = fields.Integer(
        default=10,
    )

    name = fields.Char(
        string="Source Name",
        required=True,
    )

    website = fields.Char(
        string="Website",
    )

    email = fields.Char(
        string="Email",
    )

    phone = fields.Char(
        string="Phone",
    )

    contact_person = fields.Char(
        string="Contact Person",
    )

    address = fields.Text(
        string="Address",
    )

    remarks = fields.Text(
        string="Remarks",
    )

    active = fields.Boolean(
        default=True,
    )