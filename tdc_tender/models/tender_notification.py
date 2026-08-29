from datetime import timedelta

from odoo import api, fields, models


class TenderNotification(models.Model):
    _name = "tdc.tender.notification"
    _description = "Tender Notification"
    _order = "notification_date desc, id desc"
    _rec_name = "name"

    name = fields.Char(
        string="Subject",
        required=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="For User",
        required=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Source record references
    # ------------------------------------------------------------------
    upcoming_tender_id = fields.Many2one(
        "tdc.upcoming.tender",
        string="Upcoming Tender",
    )
    tender_id = fields.Many2one(
        "tdc.tender",
        string="Tender",
    )
    worksheet_id = fields.Many2one(
        "tdc.working.sheet",
        string="Working Sheet",
    )
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Quotation",
    )
    organization_id = fields.Many2one(
        "tdc.organization",
        string="Organization",
    )

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    notification_type = fields.Selection(
        [
            ("due_date_reminder", "Due Date Reminder"),
            ("participation_pending", "Participation Pending"),
            ("payment_pending", "Payment Pending"),
            ("quotation_pending", "Quotation Pending"),
            ("tender_confirmation_pending", "Tender Confirmation Pending"),
            ("general_reminder", "General Reminder"),
        ],
        string="Type",
        required=True,
        index=True,
    )

    priority = fields.Selection(
        [
            ("0", "Low"),
            ("1", "Normal"),
            ("2", "Important"),
        ],
        string="Priority",
        default="1",
    )

    message = fields.Text(string="Message")

    due_date = fields.Date(string="Due Date")

    notification_date = fields.Date(
        string="Notification Date",
        default=fields.Date.context_today,
        index=True,
    )

    state = fields.Selection(
        [
            ("unread", "Unread"),
            ("read", "Read"),
            ("snoozed", "Snoozed"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="unread",
        index=True,
    )

    # ------------------------------------------------------------------
    # Snooze / Remind Me Later
    # ------------------------------------------------------------------
    remind_days = fields.Integer(string="Remind Me After (Days)")
    remind_me_on = fields.Date(string="Remind Me On Date")

    is_popup_shown = fields.Boolean(string="Popup Already Shown", default=False)
    is_read = fields.Boolean(string="Read", default=False)

    # ==================================================================
    # Actions (buttons on the notification record itself)
    # ==================================================================
    def action_mark_read(self):
        self.write({"state": "read", "is_read": True})

    def action_archive_notification(self):
        self.write({"state": "archived"})

    def action_snooze(self):
        """Snooze using either remind_days (relative) or remind_me_on
        (absolute date), whichever the user filled in on the form."""
        today = fields.Date.context_today(self)

        for rec in self:
            if rec.remind_me_on:
                remind_on = rec.remind_me_on
            elif rec.remind_days:
                remind_on = today + timedelta(days=rec.remind_days)
            else:
                remind_on = today + timedelta(days=1)

            rec.write({
                "state": "snoozed",
                "remind_me_on": remind_on,
                "is_popup_shown": False,
            })

    def action_open_record(self):
        """Open the record this notification is actually about."""
        self.ensure_one()
        self.action_mark_read()

        if self.notification_type == "quotation_pending" and self.tender_id:
            model, res_id, name = "tdc.tender", self.tender_id.id, "Tender"
        elif self.notification_type == "payment_pending" and self.tender_id:
            model, res_id, name = "tdc.tender", self.tender_id.id, "Tender"
        elif self.notification_type == "tender_confirmation_pending" and self.tender_id:
            model, res_id, name = "tdc.tender", self.tender_id.id, "Tender"
        elif self.sale_order_id:
            model, res_id, name = "sale.order", self.sale_order_id.id, "Quotation"
        elif self.tender_id:
            model, res_id, name = "tdc.tender", self.tender_id.id, "Tender"
        elif self.worksheet_id:
            model, res_id, name = "tdc.working.sheet", self.worksheet_id.id, "Working Sheet"
        elif self.upcoming_tender_id:
            model, res_id, name = "tdc.upcoming.tender", self.upcoming_tender_id.id, "Upcoming Tender"
        else:
            return False

        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "res_id": res_id,
            "view_mode": "form",
            "target": "current",
        }

    # ==================================================================
    # Internal helper to create/refresh a notification without duplicates
    # ==================================================================
    @api.model
    def _notify(self, *, user_id, notification_type, message, priority="1",
                due_date=None, daily_reminder=True, **refs):
        """Create a notification if one isn't already open (unread/snoozed)
        for the same user + type + source record today.
        If daily_reminder is True, a fresh row is added once per day so the
        reminder keeps resurfacing; otherwise the existing open one is left
        untouched.
        """
        today = fields.Date.context_today(self)

        domain = [
            ("user_id", "=", user_id),
            ("notification_type", "=", notification_type),
            ("state", "in", ("unread", "snoozed")),
        ]
        for field_name, value in refs.items():
            domain.append((field_name, "=", value))

        existing = self.search(domain, limit=1)

        if existing:
            if daily_reminder and existing.notification_date != today:
                # New day: refresh so it becomes visible again as a new reminder
                existing.write({
                    "notification_date": today,
                    "state": "unread",
                    "is_popup_shown": False,
                    "message": message,
                })
            # else: already has an open reminder for today (or daily
            # reminders disabled) -> do nothing, avoid duplicates
            return existing

        vals = {
            "name": message[:120],
            "user_id": user_id,
            "notification_type": notification_type,
            "message": message,
            "priority": priority,
            "due_date": due_date,
            "notification_date": today,
            "state": "unread",
        }
        vals.update(refs)
        return self.create(vals)

    def _resolve(self, notification_type, **refs):
        """Archive any open notification of this type for these source refs
        (used when the underlying condition is no longer true, e.g. a
        quotation was created or a payment was made)."""
        domain = [
            ("notification_type", "=", notification_type),
            ("state", "in", ("unread", "snoozed", "read")),
        ]
        for field_name, value in refs.items():
            domain.append((field_name, "=", value))

        self.search(domain).write({"state": "archived"})

    # ==================================================================
    # Scheduled Action entry point
    # ==================================================================
    @api.model
    def _cron_check_tender_notifications(self):
        settings = self.env["tdc.tender.notification.settings"].get_settings()
        today = fields.Date.context_today(self)

        self._wake_up_snoozed(today)
        self._check_upcoming_tenders(settings, today)
        self._check_tenders(settings, today)

    def _wake_up_snoozed(self, today):
        snoozed = self.search([
            ("state", "=", "snoozed"),
            ("remind_me_on", "<=", today),
        ])
        snoozed.write({"state": "unread", "is_popup_shown": False})

    def _check_upcoming_tenders(self, settings, today):
        upcoming_tenders = self.env["tdc.upcoming.tender"].search([
            ("state", "in", ("draft", "participated")),
            ("due_date", "!=", False),
        ])

        for ut in upcoming_tenders:
            notify_days = settings.notify_before_due
            if ut.priority == "2":
                notify_days += settings.priority_extra_days

            remind_from = ut.due_date - timedelta(days=notify_days)

            due_soon = today >= remind_from

            if ut.state == "draft":
                if due_soon:
                    self._notify(
                        user_id=ut.create_uid.id,
                        notification_type="participation_pending",
                        message=(
                            f"Tender '{ut.tender_title}' (Due: {ut.due_date}) "
                            f"has not been marked Participated yet."
                        ),
                        priority=ut.priority,
                        due_date=ut.due_date,
                        daily_reminder=settings.daily_reminder,
                        upcoming_tender_id=ut.id,
                        organization_id=ut.organization_id.id,
                    )
                    self._create_activity(settings, ut, "Participation pending for this tender.")

            elif ut.state == "participated" and not ut.tender_id:
                # Participated but the Tender record hasn't been created yet.
                self._notify(
                    user_id=ut.create_uid.id,
                    notification_type="general_reminder",
                    message=(
                        f"Tender '{ut.tender_title}' was marked Participated but no "
                        f"Tender record has been created yet."
                    ),
                    priority=ut.priority,
                    due_date=ut.due_date,
                    daily_reminder=settings.daily_reminder,
                    upcoming_tender_id=ut.id,
                    organization_id=ut.organization_id.id,
                )
                self._create_activity(settings, ut, "Create the Tender for this participated entry.")

    def _check_tenders(self, settings, today):
        tenders = self.env["tdc.tender"].search([
            ("state", "!=", "confirm"),
        ])

        for tender in tenders:
            # --- Quotation not created yet ---
            if tender.quotation_state == "not_created":
                self._notify(
                    user_id=tender.create_uid.id,
                    notification_type="quotation_pending",
                    message=f"Quotation not yet created for Tender {tender.name}.",
                    priority="1",
                    daily_reminder=settings.daily_reminder,
                    tender_id=tender.id,
                    upcoming_tender_id=tender.upcoming_tender_id.id,
                    organization_id=tender.organization_id.id,
                )
                self._create_activity(settings, tender, "Create the sales quotation for this Tender.")
            else:
                self._resolve("quotation_pending", tender_id=tender.id)

            # --- Payment pending ---
            if tender.state == "request_payment":
                self._notify(
                    user_id=tender.create_uid.id,
                    notification_type="payment_pending",
                    message=f"Tender fee still requires payment for Tender {tender.name}.",
                    priority="2",
                    daily_reminder=settings.daily_reminder,
                    tender_id=tender.id,
                    upcoming_tender_id=tender.upcoming_tender_id.id,
                    organization_id=tender.organization_id.id,
                )
                self._create_activity(settings, tender, "Tender fee payment is pending.")

            if tender.payment_state == "paid" or tender.state == "paid":
                self._resolve("payment_pending", tender_id=tender.id)

            # --- Tender stuck in draft, not yet confirmed ---
            if tender.state == "draft":
                self._notify(
                    user_id=tender.create_uid.id,
                    notification_type="tender_confirmation_pending",
                    message=f"Tender {tender.name} is still in Draft and needs to be confirmed.",
                    priority="1",
                    daily_reminder=settings.daily_reminder,
                    tender_id=tender.id,
                    upcoming_tender_id=tender.upcoming_tender_id.id,
                    organization_id=tender.organization_id.id,
                )
            else:
                self._resolve("tender_confirmation_pending", tender_id=tender.id)

    def _create_activity(self, settings, record, note):
        if not settings.enable_activity_notification:
            return
        activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        if not activity_type:
            return
        try:
            record.activity_schedule(
                activity_type_id=activity_type.id,
                summary="Tender Reminder",
                note=note,
                user_id=record.create_uid.id,
            )
        except Exception:
            # Model may not support activities in some edge case; never let
            # the cron crash because of this optional feature.
            pass

    # ==================================================================
    # Called on login / dashboard load
    # ==================================================================
    @api.model
    def get_unread_count(self):
        return self.search_count([
            ("user_id", "=", self.env.uid),
            ("state", "=", "unread"),
        ])

    @api.model
    def get_popup_notifications(self):
        settings = self.env["tdc.tender.notification.settings"].get_settings()
        if not settings.enable_popup_notification:
            return []

        notifs = self.search([
            ("user_id", "=", self.env.uid),
            ("state", "=", "unread"),
            ("is_popup_shown", "=", False),
        ])
        notifs.write({"is_popup_shown": True})

        return notifs.read([
            "name", "message", "notification_type", "priority", "due_date",
        ])
