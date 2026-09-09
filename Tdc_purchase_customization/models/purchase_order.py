# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # ------------------------------------------------------------------
    # New field: Purchase Order Type (shows before Vendor in the form)
    # ------------------------------------------------------------------
    purchase_type = fields.Selection(
        [
            ('local', 'Local Purchase'),
            ('import', 'Import Purchase'),
        ],
        string='Purchase Order Type',
        default='local',
        required=True,
        tracking=True,
        help="Local Purchase: standard RFQ flow, nothing changes.\n"
             "Import Purchase: extended flow with Proforma Invoice, "
             "Payment and Shipment tracking stages.",
    )

    # ------------------------------------------------------------------
    # Full override (not selection_add) so we control the ORDER of the
    # values. Odoo's statusbar widget displays visible values in the
    # order they appear in this list - statusbar_visible only filters
    # which ones show, it does not reorder them. That is why "proforma"
    # is placed right where we want it: after "to approve" (so the
    # Local flow order draft/sent/to approve/purchase is unaffected)
    # and before "purchase" (so the Import flow reads
    # Proforma INV -> Purchase Order -> Payment Under Process -> ...).
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=[
            ('draft', 'RFQ'),
            ('sent', 'RFQ Sent'),
            ('to approve', 'To Approve'),
            ('proforma', 'Proforma INV'),
            ('purchase', 'Purchase Order'),
            ('payment_under_process', 'Payment Under Process'),
            ('payment_completed', 'Payment Completed'),
            ('order_confirmation', 'Order Confirmation'),
            ('shipment_pickup', 'Shipment Pickup'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        copy=False,
        index=True,
        readonly=True,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # "Order Confirmation" tab fields (Import purchase only)
    # ------------------------------------------------------------------
    expected_manufacturing_time = fields.Integer(
        string='Expected Manufacturing Time (Days)')
    expected_transportation_date = fields.Date(
        string='Expected Transportation')
    custom_clearance_date = fields.Date(
        string='Custom Clearance Time')
    mode_of_transport = fields.Selection(
        [
            ('air', 'By Air'),
            ('sea', 'By Sea'),
            ('land', 'By Land'),
        ],
        string='Mode of Transport')
    order_confirmation_note = fields.Text(string='Note')
    order_confirmation_attachment_ids = fields.One2many(
        'tdc.purchase.attachment.line', 'order_id',
        domain=[('section', '=', 'order_confirmation')],
        context={'default_section': 'order_confirmation'},
        string='Attachment Lines')

    # ------------------------------------------------------------------
    # "Shipment Pickup" tab fields (Import purchase only)
    # ------------------------------------------------------------------
    shipment_pickup_status = fields.Selection(
        [
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        string='Shipment Picked Up')
    shipment_pickup_note = fields.Text(string='Note')
    expected_departure_time = fields.Datetime(
        string='Expected Time of Departure')
    expected_arrival_time = fields.Datetime(
        string='Expected Time of Arrival')
    notification_date = fields.Date(string='Notification Date')
    # Assumption: "Arrived at Destination" is a many2one to a contact /
    # location. Change comodel below (e.g. 'stock.location',
    # 'stock.warehouse') if you want it linked to something else.
    arrived_at_destination_id = fields.Many2one(
        'res.partner', string='Arrived at Destination')
    shipment_pickup_attachment_ids = fields.One2many(
        'tdc.purchase.attachment.line', 'order_id',
        domain=[('section', '=', 'shipment_pickup')],
        context={'default_section': 'shipment_pickup'},
        string='Attachment Lines')

    # ------------------------------------------------------------------
    # When user switches Local <-> Import while still in the initial
    # state, keep state in sync (draft <-> proforma).
    # ------------------------------------------------------------------
    @api.onchange('purchase_type')
    def _onchange_purchase_type(self):
        for order in self:
            if order.state in ('draft', 'proforma'):
                order.state = 'proforma' if order.purchase_type == 'import' else 'draft'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('purchase_type') == 'import' and not vals.get('state'):
                vals['state'] = 'proforma'
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Dedicated confirm action for Import orders sitting in Proforma INV.
    # We do NOT reuse core button_confirm()/its button: that core method
    # only acts on orders whose state is 'draft' or 'sent' and silently
    # skips everything else - which is why clicking the standard
    # "Confirm Order" button did nothing from the Proforma state.
    # This action moves Proforma INV straight to Purchase Order, per
    # the requested Import flow (no RFQ Sent / To Approve step).
    # ------------------------------------------------------------------
    def action_confirm_proforma(self):
        self.write({
            'state': 'purchase',
            'date_approve': fields.Datetime.now(),
        })
        for order in self:
            if order.partner_id and order.partner_id not in order.message_partner_ids:
                order.message_subscribe(order.partner_id.ids)
        return True

    # ------------------------------------------------------------------
    # New workflow buttons (Import purchase only)
    # ------------------------------------------------------------------
    def action_payment_under_process(self):
        self.write({'state': 'payment_under_process'})

    def action_payment_completed(self):
        self.write({'state': 'payment_completed'})

    def action_order_confirmation(self):
        self.write({'state': 'order_confirmation'})

    def action_shipment_pickup(self):
        self.write({'state': 'shipment_pickup'})
