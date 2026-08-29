# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    reminder_day = fields.Integer(
        string='Reminder Day',
        copy=False,
        help="Number of days before the invoice due date at which a payment "
             "reminder notification should be triggered.\n"
             "Example: Payment Terms = 10 days, Reminder Day = 3.\n"
             "When only 3 days remain before the due date, a notification "
             "is created automatically."
    )
    reminder_notified = fields.Boolean(
        string='Reminder Notified',
        default=False,
        copy=False,
        help="Technical field: True once a reminder notification has "
             "already been generated for this invoice, to avoid duplicates."
    )
    reminder_notification_count = fields.Integer(
        string='Reminder Notifications',
        compute='_compute_reminder_notification_count',
    )

    def _compute_reminder_notification_count(self):
        Notification = self.env['payment.reminder.notification']
        for move in self:
            move.reminder_notification_count = Notification.search_count(
                [('move_id', '=', move.id)]
            )

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._check_and_trigger_reminder()
        return moves

    def write(self, vals):
        res = super().write(vals)
        reset_fields = ('invoice_date_due', 'reminder_day', 'invoice_payment_term_id', 'invoice_date')
        if any(f in vals for f in reset_fields):
            for move in self:
                if move.reminder_notified:
                    move.reminder_notified = False
        self._check_and_trigger_reminder()
        return res

    def action_view_reminder_notifications(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Notifications'),
            'res_model': 'payment.reminder.notification',
            'view_mode': 'list,form',
            'domain': [('move_id', '=', self.id)],
            'context': {'default_move_id': self.id},
        }

    def _check_and_trigger_reminder(self):
        today = fields.Date.context_today(self)
        for move in self:
            if (
                move.state == 'posted'
                and move.move_type in ('out_invoice', 'out_refund')
                and move.payment_state not in ('paid', 'in_payment', 'reversed')
                and move.invoice_date_due
                and move.reminder_day > 0
                and not move.reminder_notified
            ):
                days_remaining = (move.invoice_date_due - today).days
                if days_remaining == move.reminder_day:
                    move._create_reminder_notification(days_remaining)

    def _create_reminder_notification(self, days_remaining):
        self.ensure_one()
        message = _(
            "Invoice %(name)s for %(partner)s is due on %(due)s. "
            "%(days)s day(s) remaining (Reminder Day = %(reminder)s).",
            name=self.name or self.ref or _('Draft Invoice'),
            partner=self.partner_id.display_name,
            due=self.invoice_date_due,
            days=days_remaining,
            reminder=self.reminder_day,
        )

        self.env['payment.reminder.notification'].create({
            'move_id': self.id,
            'partner_id': self.partner_id.id,
            'invoice_date_due': self.invoice_date_due,
            'reminder_day': self.reminder_day,
            'days_remaining': days_remaining,
            'message': message,
        })
        self.reminder_notified = True

        self.message_post(body=message)

        partners = self.invoice_user_id.partner_id | self.env.user.partner_id
        if partners:
            self.message_notify(
                partner_ids=partners.ids,
                subject=_('Payment Reminder: %s', self.name or self.ref or ''),
                body=message,
                subtype_xmlid='mail.mt_comment',
            )

        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'type': 'warning',
                'title': _('Payment Reminder'),
                'message': message,
                'sticky': True,
            },
        )
        return True

    @api.model
    def _cron_check_payment_reminders(self):
        moves = self.search([
            ('state', '=', 'posted'),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('payment_state', 'not in', ('paid', 'in_payment', 'reversed')),
            ('invoice_date_due', '!=', False),
            ('reminder_day', '>', 0),
            ('reminder_notified', '=', False),
        ])
        moves._check_and_trigger_reminder()
        return True