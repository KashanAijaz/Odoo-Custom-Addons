# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # ------------------------------------------------------------------
    # Fields
    # ------------------------------------------------------------------
    payroll_type = fields.Selection(
        selection=[
            ('shariah', 'Shariah Payroll System'),
            ('international', 'International Payroll System'),
        ],
        string="Payroll System",
        default='international',
        tracking=True,
        help="Shariah: every late minute and every absent day is deducted.\n"
             "International: late minutes are deducted up to 30 min; beyond "
             "30 min late the whole day is treated as absent. Leave taken "
             "on the working days bracketing a weekend (sandwich leave) is "
             "deducted for the whole block, weekend included.",
    )

    late_minutes = fields.Float(
        string="Total Late Minutes",
        readonly=True, copy=False,
        help="Sum of late-arrival minutes counted towards a per-minute "
             "deduction (i.e. minutes NOT already converted into a full "
             "day-off under the International rule).")
    late_minute_deduction = fields.Monetary(
        string="Late Minutes Deduction", readonly=True, copy=False)

    day_off_count = fields.Float(
        string="Unexcused Day-Off Count", readonly=True, copy=False,
        help="Full days with no attendance at all, plus (International "
             "only) days where check-in was more than 30 minutes late.")
    day_off_deduction = fields.Monetary(
        string="Day-Off Deduction", readonly=True, copy=False)

    sandwich_leave_days = fields.Float(
        string="Sandwich Leave Extra Days", readonly=True, copy=False,
        help="Weekend/off days added to the deduction because leave was "
             "taken on both working days bracketing the weekend "
             "(International only).")
    sandwich_leave_deduction = fields.Monetary(
        string="Sandwich Leave Deduction", readonly=True, copy=False)

    attendance_total_deduction = fields.Monetary(
        string="Total Attendance-Based Deduction",
        compute='_compute_attendance_total_deduction',
        store=True, copy=False,
        help="late_minute_deduction + day_off_deduction + "
             "sandwich_leave_deduction. Read by the "
             "ATTENDANCE_DEDUCTION salary rule.")

    daily_wage = fields.Monetary(string="Computed Daily Wage", readonly=True, copy=False)
    minute_wage = fields.Monetary(string="Computed Per-Minute Wage", readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Onchange: default the payroll type from the employee's contract
    # ------------------------------------------------------------------
    @api.onchange('employee_id', 'contract_id')
    def _onchange_employee_set_payroll_type(self):
        for slip in self:
            if slip.contract_id and slip.contract_id.payroll_type:
                slip.payroll_type = slip.contract_id.payroll_type

    # ------------------------------------------------------------------
    # Main hook: compute_sheet is the standard button/action used to
    # (re)generate payslip lines from the salary structure. We compute our
    # custom deduction figures right before the normal computation so the
    # ATTENDANCE_DEDUCTION salary rule (see data/hr_salary_rule_data.xml)
    # can read them.
    # ------------------------------------------------------------------
    def compute_sheet(self):
        for slip in self:
            if slip.payroll_type:
                slip._compute_shariah_international_deductions()
        return super().compute_sheet()

    @api.depends('late_minute_deduction', 'day_off_deduction', 'sandwich_leave_deduction')
    def _compute_attendance_total_deduction(self):
        for slip in self:
            slip.attendance_total_deduction = (
                slip.late_minute_deduction
                + slip.day_off_deduction
                + slip.sandwich_leave_deduction
            )

    # ------------------------------------------------------------------
    # Core computation
    # ------------------------------------------------------------------
    def _compute_shariah_international_deductions(self):
        self.ensure_one()
        contract = self.contract_id
        employee = self.employee_id
        if not contract or not employee or not self.date_from or not self.date_to:
            return

        calendar = contract.resource_calendar_id
        wage = contract.wage or 0.0

        # --- Wage baselines --------------------------------------------------
        # Days used to prorate a monthly wage into a single day's wage.
        # Adjust `days_in_month` sourcing to match your salary structure if
        # you already store this elsewhere (e.g. a company setting).
        days_in_month = 30.0
        daily_wage = wage / days_in_month if days_in_month else 0.0

        # Average working hours per working day, from the calendar.
        hours_per_day = calendar.hours_per_day or 8.0
        minute_wage = daily_wage / (hours_per_day * 60.0) if hours_per_day else 0.0

        self.daily_wage = daily_wage
        self.minute_wage = minute_wage

        late_minutes_total = 0.0
        day_off_count = 0.0

        working_dates = self._get_working_dates(calendar, self.date_from, self.date_to)

        for day in working_dates:
            scheduled_start = self._get_scheduled_checkin(calendar, day)
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', fields.Datetime.to_datetime(day)),
                ('check_in', '<', fields.Datetime.to_datetime(day) + timedelta(days=1)),
            ], order='check_in asc', limit=1)

            on_leave = self._is_on_approved_leave(employee, day)
            if on_leave:
                # Leave days are handled separately by the sandwich-leave
                # logic below; do not also count them as an unexcused
                # day-off here.
                continue

            if not attendances:
                # No check-in recorded at all -> unexcused absence.
                day_off_count += 1.0
                continue

            if not scheduled_start:
                continue

            check_in = attendances.check_in
            late_minutes_day = self._minutes_late(check_in, scheduled_start)
            if late_minutes_day <= 0:
                continue

            if self.payroll_type == 'shariah':
                late_minutes_total += late_minutes_day
            else:  # international
                if late_minutes_day > 30:
                    day_off_count += 1.0
                else:
                    late_minutes_total += late_minutes_day

        self.late_minutes = late_minutes_total
        self.late_minute_deduction = late_minutes_total * minute_wage
        self.day_off_count = day_off_count
        self.day_off_deduction = day_off_count * daily_wage

        if self.payroll_type == 'international':
            sandwich_days = self._compute_sandwich_leave_days(calendar, employee)
            self.sandwich_leave_days = sandwich_days
            self.sandwich_leave_deduction = sandwich_days * daily_wage
        else:
            self.sandwich_leave_days = 0.0
            self.sandwich_leave_deduction = 0.0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_working_dates(self, calendar, date_from, date_to):
        """Return the list of dates in [date_from, date_to] that the
        calendar defines as working days (regardless of attendance)."""
        dates = []
        current = date_from
        while current <= date_to:
            if self._is_calendar_working_day(calendar, current):
                dates.append(current)
            current += timedelta(days=1)
        return dates

    def _is_calendar_working_day(self, calendar, date):
        weekday = str(date.weekday())  # Odoo calendar: '0' = Monday ... '6' = Sunday
        return bool(calendar.attendance_ids.filtered(lambda a: a.dayofweek == weekday))

    def _get_scheduled_checkin(self, calendar, date):
        """Earliest scheduled check-in time (as a Datetime) for the given
        date, based on the resource.calendar.attendance lines."""
        weekday = str(date.weekday())
        lines = calendar.attendance_ids.filtered(lambda a: a.dayofweek == weekday)
        if not lines:
            return False
        earliest = min(lines, key=lambda a: a.hour_from)
        hour = int(earliest.hour_from)
        minute = int(round((earliest.hour_from - hour) * 60))
        return fields.Datetime.to_datetime(date).replace(hour=hour, minute=minute, second=0)

    def _minutes_late(self, check_in, scheduled_start):
        if not check_in or not scheduled_start:
            return 0.0
        delta = check_in - scheduled_start
        return max(0.0, delta.total_seconds() / 60.0)

    def _is_on_approved_leave(self, employee, date):
        Leave = self.env['hr.leave']
        leave = Leave.search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('date_from', '<=', fields.Datetime.to_datetime(date) + timedelta(hours=23, minutes=59)),
            ('date_to', '>=', fields.Datetime.to_datetime(date)),
        ], limit=1)
        return bool(leave)

    def _compute_sandwich_leave_days(self, calendar, employee):
        """International rule only.

        If the employee is on approved leave on the last working day before
        a weekend block AND on the first working day after that same
        weekend block, every day in the weekend block is added as an extra
        deducted day (the weekend itself is normally unpaid/neutral, but
        become deductible once "sandwiched" between two leave days).

        Example: calendar works Mon-Fri (Sat/Sun weekend). Employee takes
        leave on Friday and the following Monday -> Fri, Sat, Sun, Mon = 4
        days are deducted instead of just the 2 requested leave days (i.e.
        2 extra days are added here on top of the normal leave deduction
        already handled by the Leave/Time Off module).
        """
        extra_days = 0.0
        current = self.date_from
        visited_blocks = set()

        while current <= self.date_to:
            if self._is_calendar_working_day(calendar, current) and self._is_on_approved_leave(employee, current):
                # Walk forward through consecutive non-working (weekend) days.
                cursor = current + timedelta(days=1)
                weekend_block = []
                while cursor <= self.date_to and not self._is_calendar_working_day(calendar, cursor):
                    weekend_block.append(cursor)
                    cursor += timedelta(days=1)

                if weekend_block and cursor <= self.date_to and self._is_calendar_working_day(calendar, cursor):
                    if self._is_on_approved_leave(employee, cursor):
                        block_key = (weekend_block[0], weekend_block[-1])
                        if block_key not in visited_blocks:
                            visited_blocks.add(block_key)
                            extra_days += len(weekend_block)
            current += timedelta(days=1)

        return extra_days
