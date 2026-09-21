# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderPurchaseReferenceLine(models.TransientModel):
    _name = 'sale.order.purchase.reference.line'
    _description = 'Sale Order Purchase Reference Line'

    wizard_id = fields.Many2one('sale.order.purchase.reference.wizard', ondelete='cascade')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True)
    name = fields.Char(related='purchase_order_id.name', string='Reference')
    date_order = fields.Datetime(related='purchase_order_id.date_order', string='Date')
    amount_total = fields.Monetary(related='purchase_order_id.amount_total', string='Amount')
    currency_id = fields.Many2one(related='purchase_order_id.currency_id')
    state = fields.Selection(related='purchase_order_id.state', string='Status')
    selected = fields.Boolean(string='Selected', default=True)


class SaleOrderPurchaseReferenceWizard(models.TransientModel):
    _name = 'sale.order.purchase.reference.wizard'
    _description = 'Sale Order Purchase Reference Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    line_ids = fields.One2many(
        'sale.order.purchase.reference.line', 'wizard_id', string='Purchase Orders'
    )

    def action_select_all(self):
        self.ensure_one()
        self.line_ids.write({'selected': True})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Reference',
            'res_model': 'sale.order.purchase.reference.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_print_pdf(self):
        self.ensure_one()
        return self.env.ref('tdc_uom_calculation.action_report_purchase_reference').report_action(self)