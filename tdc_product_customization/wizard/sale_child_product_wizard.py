# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderChildProductWizard(models.TransientModel):
    _name = 'sale.order.child.product.wizard'
    _description = 'Add Child Products to Sale Order'

    order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    parent_product_tmpl_id = fields.Many2one(
        'product.template', string='Parent Product', required=True
    )
    line_ids = fields.One2many(
        'sale.order.child.product.wizard.line', 'wizard_id',
        string='Child Products',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        parent_id = res.get('parent_product_tmpl_id')
        if parent_id and 'line_ids' in fields_list:
            parent = self.env['product.template'].browse(parent_id)
            res['line_ids'] = [
                (0, 0, {'product_tmpl_id': child.id})
                for child in parent.child_product_ids
            ]
        return res
    def action_add_selected(self):
        self.ensure_one()
        selected_lines = self.line_ids.filtered(lambda l: l.to_add and not l.added)
        if not selected_lines:
            return {'type': 'ir.actions.act_window_close'}
        for line in selected_lines:
            line.action_add_to_order()
        return {'type': 'ir.actions.act_window_close'}
class SaleOrderChildProductWizardLine(models.TransientModel):
    _name = 'sale.order.child.product.wizard.line'
    _description = 'Sale Order Child Product Wizard Line'

    wizard_id = fields.Many2one(
        'sale.order.child.product.wizard', ondelete='cascade'
    )
    product_tmpl_id = fields.Many2one('product.template', string='Product')
    name = fields.Char(related='product_tmpl_id.name', readonly=True)
    list_price = fields.Float(related='product_tmpl_id.list_price', readonly=True)
    added = fields.Boolean(string='Added', default=False, readonly=True)
    to_add = fields.Boolean(string='Select', default=False)   # 👈 NAYA FIELD

    def action_add_to_order(self):
        self.ensure_one()
        order = self.wizard_id.order_id
        product = self.product_tmpl_id.product_variant_id
        order.write({
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,
            })]
        })
        self.added = True
        return True