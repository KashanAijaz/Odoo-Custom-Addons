# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # NOTE: If you already maintain HS Codes / CD / ACD / RD in a separate
    # "hs.code" model (e.g. from the TDC HS Code module), replace the four
    # fields below with:
    #
    #   hs_code_id = fields.Many2one('hs.code', string='HS Code')
    #   tdc_cd = fields.Float(related='hs_code_id.cd', store=True, readonly=True)
    #   tdc_acd = fields.Float(related='hs_code_id.acd', store=True, readonly=True)
    #   tdc_rd = fields.Float(related='hs_code_id.rd', store=True, readonly=True)
    #
    # and add that module's technical name to the 'depends' list in
    # __manifest__.py. As shipped, these are simple fields kept on the
    # product itself so the module installs standalone.

    tdc_hs_code = fields.Char(
        string='HS Code',
        help='Format: 0000.0000 (4 digits, a dot, 4 digits).'
    )
    tdc_cd = fields.Float(
        string='CD (%)', digits=(16, 2),
        help='Customs Duty percentage applicable on this product.'
    )
    tdc_acd = fields.Float(
        string='ACD (%)', digits=(16, 2),
        help='Additional Customs Duty percentage applicable on this product.'
    )
    tdc_rd = fields.Float(
        string='RD (%)', digits=(16, 2),
        help='Regulatory Duty percentage applicable on this product.'
    )
