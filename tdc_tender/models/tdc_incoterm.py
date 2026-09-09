from odoo import fields, models


class TdcIncoterms(models.Model):
    _name = 'tdc.incoterms'
    _description = 'TDC Incoterms Master'
    _rec_name = 'name'  # Orders them alphabetically by code (e.g., CFR, CIF, FOB)

    code = fields.Char(string='Code', required=True, size=3, help="3-letter Incoterm code (e.g., FOB, CIF)")
    name = fields.Char(string='Name', required=True, help="Full name of the term (e.g., Free On Board)")
    active = fields.Boolean(default=True, help="Set to False to archive the incoterm without deleting it")