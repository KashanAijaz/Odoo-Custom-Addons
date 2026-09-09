# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    hs_code_id = fields.Many2one(
        'hs.code',
        string='HS Code',
        compute='_compute_hs_code_id',
        store=True,
        readonly=False,
        precompute=True,
    )

    model_no_id = fields.Many2one(
        'product.model',
        string='Model No',
        compute='_compute_model_no_id',
        store=True,
        readonly=False,
        precompute=True,
    )

    serial_no_id = fields.Many2one(
        'product.serial',
        string='Serial No',
        compute='_compute_serial_no_id',
        store=True,
        readonly=False,
        precompute=True,
    )

    @api.depends('product_id')
    def _compute_hs_code_id(self):
        for line in self:
            if line.product_id:
                line.hs_code_id = line.product_id.hs_code_id
            elif not line.hs_code_id:
                line.hs_code_id = False

    @api.depends('product_id')
    def _compute_model_no_id(self):
        for line in self:
            if line.product_id:
                line.model_no_id = line.product_id.model_no_id
            elif not line.model_no_id:
                line.model_no_id = False

    @api.depends('product_id')
    def _compute_serial_no_id(self):
        for line in self:
            if line.product_id:
                line.serial_no_id = line.product_id.serial_no_id
            elif not line.serial_no_id:
                line.serial_no_id = False