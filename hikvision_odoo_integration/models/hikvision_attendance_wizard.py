# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HikvisionAttendanceWizard(models.TransientModel):
    _name = 'hikvision.attendance.wizard'
    _description = 'Download Attendance by Date Range'

    device_id = fields.Many2one(
        'hikvision.device', string="Device", required=True,
        default=lambda self: self.env.context.get('active_id')
    )
    start_date = fields.Date(
        string="From Date", required=True,
        default=lambda self: fields.Date.today().replace(day=1)
    )
    end_date = fields.Date(
        string="To Date", required=True,
        default=fields.Date.today
    )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise UserError(_("Start Date cannot be after End Date."))

    def action_download(self):
        self.ensure_one()
        return self.device_id.download_all_attendance(
            start_date=self.start_date,
            end_date=self.end_date,
        )