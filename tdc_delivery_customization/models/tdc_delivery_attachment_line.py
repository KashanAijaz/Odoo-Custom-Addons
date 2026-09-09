# -*- coding: utf-8 -*-
from odoo import fields, models


class TDCDeliveryAttachmentLine(models.Model):
    _name = "tdc.delivery.attachment.line"
    _description = "Delivery Order Attachment Line"

    picking_id = fields.Many2one(
        "stock.picking",
        string="Delivery Order",
        required=True,
        ondelete="cascade",
    )

    attachment = fields.Binary(string="Attachment", attachment=True)
    attachment_filename = fields.Char(string="Attachment Name")

    name = fields.Char(string="Name")
    notes = fields.Text(string="Notes")
    details = fields.Text(string="Details")

    user_id = fields.Many2one(
        "res.users",
        string="Added By",
        default=lambda self: self.env.user,
        readonly=True,
    )
    date = fields.Date(
        string="Date",
        default=fields.Date.today,
        readonly=True,
    )
