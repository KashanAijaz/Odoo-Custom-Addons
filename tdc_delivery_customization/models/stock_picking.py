# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    state = fields.Selection(
        selection_add=[
            ("draft", "Draft"),
            ("waiting", "Waiting Another Operation"),
            ("confirmed", "Waiting"),
            ("assigned", "Ready"),
            ("done", "Delivery Out"),
            ("delivery_reciept", "Delivery Receipt"),
            ("installation_under_process", "Installation Under Process"),
            ("installation_complete", "Installation Complete"),
            ("satisfactory_complete", "Satisfactory Completed"),
            ("cancel", "Cancelled"),
        ],
        ondelete={
            "delivery_reciept": "cascade",
            "installation_under_process": "cascade",
            "installation_complete": "cascade",
            "satisfactory_complete": "cascade",
        },
    )

    # ---------- Delivery Type (Delivery Receipt state) ----------
    delivery_type = fields.Selection(
        [
            ("by_hand", "By Hand"),
            ("by_courier", "By Courier"),
            ("bilti_transport", "Bilti Transport"),
            ("customer_pickup", "Customer Self Pickup"),
        ],
        string="Delivery Type",
        copy=False,
    )

    responsible_person_name = fields.Char(string="Responsible Person Name")
    receiver_name = fields.Char(string="Receiver Name")
    receiver_designation = fields.Char(string="Designation")
    receiver_department = fields.Char(string="Department Name")
    receiver_contact_info = fields.Char(string="Contact Info")
    delivery_date = fields.Date(string="Date / Day")
    delivery_address_note = fields.Text(string="Delivery Address")

    courier_company_id = fields.Many2one(
        "res.partner", string="Courier Company",
        domain="[('is_company', '=', True)]",
    )
    courier_service_type = fields.Selection(
        [
            ("slow", "Slow (Overland)"),
            ("normal", "Normal"),
            ("fast", "Fast (Overnight)"),
        ],
        string="Service Type",
    )
    courier_tracking_number = fields.Char(string="Tracking Number")
    courier_booking_date = fields.Date(string="Booking Date")
    courier_shipping_amount = fields.Float(string="Shipping Amount / Courier Charges")

    pickup_location = fields.Char(string="Pickup Location")
        # ---------- Bilti Transport fields ----------
    bilti_service_provider_name = fields.Char(string="Service Provider Name")
    bilti_truck_train_number = fields.Char(string="Truck No / Train Boggi Number")
    bilti_receipt_date = fields.Date(string="Receipt Date")
    bilti_delivery_date = fields.Date(string="Delivery Date of Bilty")
    bilti_expected_arrival_date = fields.Date(string="Expected Arrival at Destination Date")

    # ---------- Installation Under Process fields ----------
    installation_by = fields.Selection(
        [
            ("self", "It Self"),
            ("end_user", "End User"),
            ("welkin_team", "Welkin's Team"),
        ],
        string="Installation By",
        copy=False,
    )
    technical_person_name = fields.Char(string="Technical Person Name")
    installation_city = fields.Char(string="City")
    installation_office = fields.Char(string="Office")
    installation_designation = fields.Char(string="Designation")
    installation_department = fields.Char(string="Department")
    installation_start_date = fields.Date(string="Date of Starting Installation")
    installation_notes = fields.Text(string="Notes")

    # ---------- Installation Complete fields ----------
    installation_completion_date = fields.Date(string="Date Completion")
    installation_total_days = fields.Integer(
        string="Total Days",
        compute="_compute_installation_total_days",
        store=True,
    )
    customer_feedback = fields.Text(string="Customer Feedback")

    # ---------- Attachment Lines (One2many to tdc.delivery.attachment.line) ----------
    tdc_attachment_line_ids = fields.One2many(
        "tdc.delivery.attachment.line",
        "picking_id",
        string="Attachments",
    )

    # ---------- Compute methods ----------
    @api.depends("installation_start_date", "installation_completion_date")
    def _compute_installation_total_days(self):
        for picking in self:
            if picking.installation_start_date and picking.installation_completion_date:
                delta = picking.installation_completion_date - picking.installation_start_date
                picking.installation_total_days = delta.days
            else:
                picking.installation_total_days = 0

    # ---------- State transition actions ----------
    def action_set_delivery_receipt(self):
        self.write({"state": "delivery_reciept"})

    def action_set_installation_under_process(self):
        self.write({"state": "installation_under_process"})

    def action_set_installation_complete(self):
        self.write({"state": "installation_complete"})

    def action_set_satisfactory_complete(self):
        self.write({"state": "satisfactory_complete"})