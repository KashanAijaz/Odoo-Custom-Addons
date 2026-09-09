# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    has_child_products = fields.Boolean(
        string='Has Child Products',
        compute='_compute_has_child_products',
    )

    @api.depends('product_id.product_tmpl_id.child_product_ids')
    def _compute_has_child_products(self):
        for line in self:
            line.has_child_products = bool(
                line.product_id.product_tmpl_id.child_product_ids
            )

    def action_open_child_products_wizard(self):
        """Line k 'Child Products' button se wizard khulta hai. User apni marzi
        se decide karega k kaun sa child product order mein add karna hai."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Child Products',
            'res_model': 'purchase.order.child.product.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.order_id.id,
                'default_parent_product_tmpl_id': self.product_id.product_tmpl_id.id,
            },
        }
