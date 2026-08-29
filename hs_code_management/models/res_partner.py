from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_vendor_type = fields.Selection([
        ('welkin', 'Welkin'),
        ('athar', 'Athar'),
    ], string='Vendor Type')