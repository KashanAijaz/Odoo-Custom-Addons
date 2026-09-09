# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    hs_code_id = fields.Many2one(
        related='product_id.product_tmpl_id.hs_code_id',
        string='HS Code',
        store=True,
        readonly=True,
    )

    model_no_id = fields.Many2one(
        'product.model',
        related='product_id.product_tmpl_id.model_no_id',
        string='Model No',
        store=True,
        readonly=True,
    )

    serial_no_id = fields.Many2one(
        'product.serial',
        related='product_id.product_tmpl_id.serial_no_id',
        string='Serial No',
        store=True,
        readonly=True,
    )