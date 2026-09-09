# -*- coding: utf-8 -*-
from odoo import models, fields


class TdcPurchaseAttachmentLine(models.Model):
    _name = 'tdc.purchase.attachment.line'
    _description = 'Purchase Order Attachment Line'

    order_id = fields.Many2one(
        'purchase.order', string='Purchase Order',
        required=True, ondelete='cascade')

    section = fields.Selection(
        [
            ('order_confirmation', 'Order Confirmation'),
            ('shipment_pickup', 'Shipment Pickup'),
        ],
        string='Section', required=True)

    payment_attachment = fields.Binary(
        string="Attachment",
        attachment=True,
    )
    payment_attachment_filename = fields.Char(
        string="Attachment Name"
    )
    payment_note = fields.Text(
        string="Note"
    )
