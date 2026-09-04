# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrderChildProductWizard(models.TransientModel):
    _name = 'purchase.order.child.product.wizard'
    _description = 'Add Child Products to Purchase Order'

    order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True)
    parent_product_tmpl_id = fields.Many2one(
        'product.template', string='Parent Product', required=True
    )
    line_ids = fields.One2many(
        'purchase.order.child.product.wizard.line', 'wizard_id',
        string='Child Products',
        compute='_compute_line_ids', store=True, readonly=False,
    )

    @api.depends('parent_product_tmpl_id')
    def _compute_line_ids(self):
        for wizard in self:
            lines = [
                (0, 0, {'product_tmpl_id': child.id})
                for child in wizard.parent_product_tmpl_id.child_product_ids
            ]
            wizard.line_ids = lines

    # 👇 NAYA METHOD
    def action_add_selected(self):
        self.ensure_one()
        selected_lines = self.line_ids.filtered(lambda l: l.to_add and not l.added)
        if not selected_lines:
            return {'type': 'ir.actions.act_window_close'}
        for line in selected_lines:
            line.action_add_to_order()
        return {'type': 'ir.actions.act_window_close'}


class PurchaseOrderChildProductWizardLine(models.TransientModel):
    _name = 'purchase.order.child.product.wizard.line'
    _description = 'Purchase Order Child Product Wizard Line'

    wizard_id = fields.Many2one(
        'purchase.order.child.product.wizard', ondelete='cascade'
    )
    product_tmpl_id = fields.Many2one(
        'product.template', string='Product', readonly=True
    )
    name = fields.Char(related='product_tmpl_id.name', readonly=True)
    list_price = fields.Float(related='product_tmpl_id.list_price', readonly=True)
    added = fields.Boolean(string='Added', default=False, readonly=True)
    to_add = fields.Boolean(string='Select', default=False)   # 👈 NAYA FIELD

    # def action_add_to_order(self):
    #     self.ensure_one()
    #     wizard = self.wizard_id
    #     product = self.product_tmpl_id.product_variant_id
    #     self.env['purchase.order.line'].create({
    #         'order_id': wizard.order_id.id,
    #         'product_id': product.id,
    #         'name': product.display_name,        # required hai purchase me
    #         'product_qty': 1,
    #         'product_uom': product.uom_po_id.id,  # ye bhi required hota hai
    #         'price_unit': product.standard_price,
    #         'date_planned': fields.Datetime.now(),
    #     })
    #     self.added = True
    #     return True

    def action_add_to_order(self):
        self.ensure_one()
        wizard = self.wizard_id
        product = self.product_tmpl_id.product_variant_id
        self.env['purchase.order.line'].create({
            'order_id': wizard.order_id.id,
            'product_id': product.id,
            # 'name': product.name,          # required hai
            'product_qty': 1,
            'product_uom_id': product.uom_id.id,   # required
            'price_unit': product.standard_price,
            'date_planned': fields.Datetime.now(),
        })
        self.added = True
        return True