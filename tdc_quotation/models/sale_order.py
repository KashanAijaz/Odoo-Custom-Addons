# -*- coding: utf-8 -*-
from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # States that should use the "QT" (Quotation) series
    _TDC_QT_STATES = ('draft', 'sent', 'cancel')
    # States that should use the "SO" (Sale Order) series
    _TDC_SO_STATES = ('sale', 'done')  # 'done' kept for backward compatibility with older DBs

    def _tdc_get_sequence_info(self, state):
        """Return (sequence_code, prefix) depending on order state."""
        if state in self._TDC_SO_STATES:
            return 'tdc.quotation.so', 'SO'
        return 'tdc.quotation.qt', 'QT'

    def _tdc_compute_name(self, state):
        """Get next value from the right ir.sequence for the given state."""
        seq_code, _prefix = self._tdc_get_sequence_info(state)
        return self.env['ir.sequence'].sudo().next_by_code(seq_code) or '/'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Only override when Odoo would otherwise use the default 'New'
            if not vals.get('name') or vals.get('name') == 'New':
                state = vals.get('state', 'draft')
                vals['name'] = self._tdc_compute_name(state)
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            for order in self:
                seq_code, prefix = order._tdc_get_sequence_info(order.state)
                # Only rename if the current name does not already belong
                # to the correct series (avoids burning sequence numbers
                # every time write() is called without an actual series change)
                if not order.name or not order.name.startswith(prefix):
                    new_name = order._tdc_compute_name(order.state)
                    # avoid recursive write loop, use SQL-safe super call
                    super(SaleOrder, order).write({'name': new_name})
        return res
