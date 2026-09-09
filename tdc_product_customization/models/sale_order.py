# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    has_child_products = fields.Boolean(
        string='Has Child Products',
        compute='_compute_has_child_products',
    )

    @api.depends('product_template_id.child_product_ids')
    def _compute_has_child_products(self):
        for line in self:
            line.has_child_products = bool(line.product_template_id.child_product_ids)

    def action_open_child_products_wizard(self):
        self.ensure_one()
        if not isinstance(self.id, int):
            raise UserError("Please save the quotation before adding child products.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Child Products',
            'res_model': 'sale.order.child.product.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.order_id.id,
                'default_parent_product_tmpl_id': self.product_template_id.id,
            },
        }