from odoo import fields, models

class TdcCurrency(models.Model):
    _name = 'tdc.currency'
    _description = 'TDC Currency'

    name = fields.Char(
        string='Currency Name',
        required=True
    )
    
    symbol = fields.Char(
        string='Symbol',
        required=True
    )