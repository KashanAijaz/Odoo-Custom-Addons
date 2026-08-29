from odoo import fields , models


class Instruments(models.Model):
    _name = "tdc.instruments"
    _description = "Organization"
    _rec_name = "instrument_name"

    instrument_name = fields.Char(
        string="Instrument",
        required=True,
    )
    active = fields.Boolean(default=True)
    details = fields.Text()