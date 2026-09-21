# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    qty_in_ft = fields.Float(
        string='Qty in Ft.',
        digits=(16, 4),
    )
    qty_in_kg = fields.Float(
        string='Qty in Kg.',
        digits=(16, 4),
    )

    uom_is_weight = fields.Boolean(compute='_compute_uom_is_weight')

    @api.depends('product_uom_id')
    def _compute_uom_is_weight(self):
        for line in self:
            name = (line.product_uom_id.name or '').strip().lower()
            line.uom_is_weight = bool(line.product_uom_id) and name in ('ft', 'kg')

    product_weight_kg_ft = fields.Float(
        related='product_id.weight_kg_ft',
        string='Weight Kg./Ft.',
        store=False,
        readonly=True,
        digits=(16, 4),
    )

    is_in_ft = fields.Boolean(string='In Ft')
    is_in_kg = fields.Boolean(string='In Kg')

    @api.onchange('is_in_ft')
    def _onchange_is_in_ft(self):
        for line in self:
            if line.is_in_ft:
                line.is_in_kg = False
                line.qty_in_kg = line.qty_in_ft * line.product_weight_kg_ft
                line.product_qty = line.qty_in_ft
            else:
                line.qty_in_ft = 0.0

    @api.onchange('is_in_kg')
    def _onchange_is_in_kg(self):
        for line in self:
            if line.is_in_kg:
                line.is_in_ft = False
                line.qty_in_ft = (line.qty_in_kg / line.product_weight_kg_ft) if line.qty_in_kg and line.product_weight_kg_ft else 0.0
                line.product_qty = line.qty_in_ft
            else:
                line.qty_in_kg = 0.0

    @api.onchange('qty_in_ft')
    def _onchange_qty_in_ft(self):
        for line in self:
            if line.is_in_ft:
                line.product_qty = line.qty_in_ft
                line.qty_in_kg = line.qty_in_ft * line.product_weight_kg_ft

    @api.onchange('qty_in_kg')
    def _onchange_qty_in_kg(self):
        for line in self:
            if line.is_in_kg:
                line.qty_in_ft = (line.qty_in_kg / line.product_weight_kg_ft) if line.qty_in_kg and line.product_weight_kg_ft else 0.0
                line.product_qty = line.qty_in_ft