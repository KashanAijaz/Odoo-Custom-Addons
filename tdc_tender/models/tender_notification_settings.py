from odoo import api, fields, models


class TenderNotificationSettings(models.Model):
    _name = "tdc.tender.notification.settings"
    _description = "Tender Notification Settings"

    name = fields.Char(default="Notification Settings", readonly=True)

    notify_before_due = fields.Integer(
        string="Notify Before Due (Days)",
        default=3,
        help="How many days before due_date reminders should start.",
    )

    daily_reminder = fields.Boolean(
        string="Repeat Daily Until Done",
        default=True,
        help="Send a fresh reminder every day until the related task is completed.",
    )

    priority_extra_days = fields.Integer(
        string="Extra Days for Important Tenders",
        default=2,
        help="Extra days added on top of 'Notify Before Due' for tenders "
             "where priority = Important, so they get earlier reminders.",
    )

    enable_popup_notification = fields.Boolean(
        string="Popup Notification After Login",
        default=True,
    )

    enable_dashboard_counter = fields.Boolean(
        string="Dashboard Unread Counter",
        default=True,
    )

    enable_email_notification = fields.Boolean(
        string="Email Notifications (Future)",
        default=False,
        help="Reserved for future email integration.",
    )

    enable_activity_notification = fields.Boolean(
        string="Create Odoo Activities",
        default=False,
        help="When enabled, an Odoo Activity (mail.activity) is also created "
             "on the source record whenever a notification is generated.",
    )

    @api.model
    def get_settings(self):
        """Return the single settings record, creating it with defaults
        the first time it is needed (e.g. first cron run or first menu open)."""
        settings = self.search([], limit=1)
        if not settings:
            settings = self.create({})
        return settings

    def action_open_settings(self):
        settings = self.get_settings()
        return {
            "type": "ir.actions.act_window",
            "name": "Notification Settings",
            "res_model": "tdc.tender.notification.settings",
            "view_mode": "form",
            "res_id": settings.id,
            "target": "current",
        }
