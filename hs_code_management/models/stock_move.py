# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

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
        for move in self:
            if move.product_id:
                move.hs_code_id = move.product_id.hs_code_id
            elif not move.hs_code_id:
                move.hs_code_id = False

    @api.depends('product_id')
    def _compute_model_no_id(self):
        for move in self:
            if move.product_id:
                move.model_no_id = move.product_id.model_no_id
            elif not move.model_no_id:
                move.model_no_id = False

    @api.depends('product_id')
    def _compute_serial_no_id(self):
        for move in self:
            if move.product_id:
                move.serial_no_id = move.product_id.serial_no_id
            elif not move.serial_no_id:
                move.serial_no_id = False