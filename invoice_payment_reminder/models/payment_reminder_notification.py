# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PaymentReminderNotification(models.Model):
    _name = 'payment.reminder.notification'
    _description = 'Invoice Payment Reminder Notification'
    _order = 'create_date desc'
    _rec_name = 'message'

    move_id = fields.Many2one(
        'account.move', string='Invoice', required=True,
        ondelete='cascade', index=True,
    )
    partner_id = fields.Many2one('res.partner', string='Customer')
    invoice_date_due = fields.Date(string='Due Date')
    reminder_day = fields.Integer(string='Reminder Day')
    days_remaining = fields.Integer(string='Days Remaining')
    message = fields.Char(string='Message')
    is_read = fields.Boolean(string='Read', default=False)
    company_id = fields.Many2one(
        'res.company', string='Company',
        related='move_id.company_id', store=True,
    )

    def action_mark_as_read(self):
        self.write({'is_read': True})

    def action_open_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
