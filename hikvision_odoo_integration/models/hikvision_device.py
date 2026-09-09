# -*- coding: utf-8 -*-
################################################################################
#
# Techo Digi Codes
#
################################################################################
import json
import time as time_module
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, date, time as dt_time
import pytz
import requests
from requests.auth import HTTPDigestAuth
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import UserError, ValidationError


class HikvisionDevice(models.Model):
    """Model for managing Hikvision biometric devices."""

    _name = 'hikvision.device'
    _inherit = ['mail.thread']
    _description = 'Hikvision Biometric Device'

    name = fields.Char(help='Name of the Biometric Device', required=True)
    ip_address = fields.Char("Device IP", help='The IP address of the Device', required=True)
    username = fields.Char("Username", help="Username of the device", required=True)
    password = fields.Char("Password", help="Password of the device", required=True)
    image = fields.Image()
    device_name = fields.Char("Device Name", help='Name of the Device')
    device_id = fields.Char("Device Id", help="Id of the the device")
    device_model = fields.Char("Model", help="Model of the device")
    device_serial_no = fields.Char("Serial No", help="Serial No of the device")
    device_mac_address = fields.Char(string='Device Mac ID', help='Mac ID of the Device')

    def _get_api_config(self, endpoint=""):
        """Get API configuration for device requests."""
        url = f"http://{self.ip_address}{endpoint}"
        auth = HTTPDigestAuth(self.username, self.password)
        headers = {"Content-Type": "application/json"}
        return url, auth, headers
    def _http_error_with_body(self, response, error):
        """Build a UserError that includes the device's own error text,
        not just the generic requests exception message."""
        try:
            body = response.text
        except Exception:
            body = "(no response body)"
        return exceptions.UserError(
            f"HTTP error occurred: {error}\nDevice response: {body}"
        )
    def test_connection(self):
        """Test connection and fetch device details."""
        for device in self:
            url = f"http://{device.ip_address}/ISAPI/System/deviceInfo"
            try:
                response = requests.get(url, auth=HTTPDigestAuth(device.username, device.password))
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    ns_uri = root.tag[root.tag.find("{") + 1:root.tag.find("}")]
                    ns = {'ns': ns_uri}
                    device.device_name = root.findtext('ns:deviceName', namespaces=ns)
                    device.device_id = root.findtext('ns:deviceID', namespaces=ns)
                    device.device_model = root.findtext('ns:model', namespaces=ns)
                    device.device_serial_no = root.findtext('ns:serialNumber', namespaces=ns)
                    device.device_mac_address = root.findtext('ns:macAddress', namespaces=ns)
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Successfully Connected',
                            'type': 'success',
                            'sticky': False
                        }
                    }
            except Exception as error:
                raise ValidationError(f'{error}')

    def fetch_attendance(self, start_date=None, end_date=None):
        """Fetch attendance events within date range."""
        if not self.ip_address:
            raise exceptions.UserError("Device IP address is not configured.")
        if not self.username or not self.password:
            raise exceptions.UserError("Device credentials are not configured.")

        user_tz = self.env.user.tz or "UTC"
        local_tz = pytz.timezone(user_tz)

        if not start_date or not end_date:
            today = datetime.now(local_tz).date()
            start_date = today
            end_date = today

        start_datetime = local_tz.localize(datetime.combine(start_date, dt_time.min))
        end_datetime = local_tz.localize(datetime.combine(end_date, dt_time.max))

        start_utc = start_datetime.astimezone(pytz.UTC)
        end_utc = end_datetime.astimezone(pytz.UTC)

        url, auth, headers = self._get_api_config("/ISAPI/AccessControl/AcsEvent?format=json")

        payload_template = {
            "AcsEventCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": 30,
                "major": 5,
                "minor": 0,
                "startTime": start_utc.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "endTime": end_utc.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            }
        }

        all_events = []
        position = 0
        total_matches = None

        while True:
            payload_template["AcsEventCond"]["searchResultPosition"] = position
            response = None
            try:
                response = requests.post(url, auth=auth, json=payload_template, headers=headers, timeout=10)
                response.raise_for_status()
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    raise exceptions.UserError(f"Invalid JSON response from device: {response.text}")

                events = data.get('AcsEvent', {}).get('InfoList', [])
                if total_matches is None:
                    total_matches = data.get('AcsEvent', {}).get('totalMatches', 0)

                if not events:
                    break

                all_events.extend(events)

                if len(events) < payload_template["AcsEventCond"]["maxResults"]:
                    break

                position += payload_template["AcsEventCond"]["maxResults"]

                if total_matches and len(all_events) >= total_matches:
                    break

            except requests.exceptions.ConnectionError as e:
                raise exceptions.UserError(f"Failed to connect to the device at {self.ip_address}: {str(e)}")
            except requests.exceptions.HTTPError as e:
                raise self._http_error_with_body(response, e)
            except requests.exceptions.RequestException as e:
                raise exceptions.UserError(f"Error communicating with the device: {str(e)}")

        return all_events
    def fetch_all_attendance(self, start_date=None, end_date=None):
        """Fetch attendance events within an optional date range.
        If no dates given, falls back to last 730 days + next 30 days."""
        if not self.ip_address:
            raise exceptions.UserError("Device IP address is not configured.")
        if not self.username or not self.password:
            raise exceptions.UserError("Device credentials are not configured.")

        if start_date and end_date:
            user_tz = self.env.user.tz or "UTC"
            local_tz = pytz.timezone(user_tz)
            start_dt_local = local_tz.localize(datetime.combine(start_date, dt_time.min))
            end_dt_local = local_tz.localize(datetime.combine(end_date, dt_time.max))
            start_utc = start_dt_local.astimezone(pytz.UTC)
            end_utc = end_dt_local.astimezone(pytz.UTC)
        else:
            now = datetime.now(pytz.UTC)
            start_utc = now - timedelta(days=730)
            end_utc = now + timedelta(days=30)

        all_events = []
        current_date = start_utc

        job = self.env.context.get('job')
        total_chunks = 0
        tmp = start_utc
        while tmp < end_utc:
            total_chunks += 1
            tmp = min(tmp + timedelta(days=3), end_utc)
        processed_chunks = 0

        while current_date < end_utc:
            chunk_end = min(current_date + timedelta(days=3), end_utc)

            try:
                chunk_events = self._fetch_attendance_chunk(current_date, chunk_end)
                all_events.extend(chunk_events)
                processed_chunks += 1

                if job:
                    try:
                        if hasattr(job, 'set_progress'):
                            job.set_progress(processed_chunks, total=total_chunks)
                        elif hasattr(job, 'progress'):
                            job.progress = min(100, int(processed_chunks * 100 / total_chunks))
                    except Exception:
                        pass

                time_module.sleep(0.5)

            except Exception:
                continue

            current_date = chunk_end

        return all_events

    def _fetch_attendance_chunk(self, start_date, end_date):
        """Fetch attendance for a date range chunk."""
        url, auth, headers = self._get_api_config("/ISAPI/AccessControl/AcsEvent?format=json")

        payload_template = {
            "AcsEventCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": 100,
                "major": 5,
                "minor": 0,
                "startTime": start_date.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "endTime": end_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            }
        }

        chunk_events = []
        position = 0
        total_matches = None

        while True:
            payload_template["AcsEventCond"]["searchResultPosition"] = position
            response = None
            try:
                response = requests.post(url, auth=auth, json=payload_template, headers=headers, timeout=30)
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    if response.status_code == 401:
                        try:
                            test_url, test_auth, _ = self._get_api_config("/ISAPI/System/deviceInfo")
                            requests.get(test_url, auth=test_auth, timeout=10)
                        except Exception:
                            pass
                        response = requests.post(url, auth=auth, json=payload_template, headers=headers, timeout=30)
                        response.raise_for_status()
                    else:
                        raise self._http_error_with_body(response, e)
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    raise exceptions.UserError(f"Invalid JSON response from device: {response.text}")

                events = data.get('AcsEvent', {}).get('InfoList', [])
                if total_matches is None:
                    total_matches = data.get('AcsEvent', {}).get('totalMatches', 0)

                if not events:
                    break

                chunk_events.extend(events)

                if len(events) < payload_template["AcsEventCond"]["maxResults"]:
                    break

                position += payload_template["AcsEventCond"]["maxResults"]

                if total_matches and len(chunk_events) >= total_matches:
                    break

            except requests.exceptions.ConnectionError as e:
                raise exceptions.UserError(f"Failed to connect to the device at {self.ip_address}: {str(e)}")
            except requests.exceptions.Timeout as e:
                raise exceptions.UserError(f"Request timed out: {str(e)}")
            except requests.exceptions.RequestException as e:
                raise exceptions.UserError(f"Error communicating with the device: {str(e)}")

        return chunk_events
    def fetch_and_create_attendance(self):
        """Download TODAY's attendance immediately (no job queue) and open all
        attendance records for today in a list view."""
        self.ensure_one()

        self.message_post(body=_("Step 1/4: Connecting to device and fetching today's attendance events..."))
        events = self.fetch_attendance()
        self.message_post(body=_("Step 2/4: Fetched %s event(s) from the device.") % len(events))

        self.message_post(body=_("Step 3/4: Syncing employees from device..."))
        self.fetch_employees()

        self.message_post(body=_("Step 4/4: Processing events and creating/updating attendance records..."))
        created_ids, updated_ids, skipped_count = self._process_attendance_events(events)

        self.message_post(
            body=_("Done. Created %s record(s), updated %s record(s), skipped %s event(s).")
            % (len(created_ids), len(updated_ids), skipped_count)
        )

        # Get today's date range in UTC for database query
        user_tz = self.env.user.tz or "UTC"
        local_tz = pytz.timezone(user_tz)
        today = datetime.now(local_tz).date()
        
        start_datetime = local_tz.localize(datetime.combine(today, dt_time.min))
        end_datetime = local_tz.localize(datetime.combine(today, dt_time.max))
        
        start_utc = start_datetime.astimezone(pytz.UTC).replace(tzinfo=None)
        end_utc = end_datetime.astimezone(pytz.UTC).replace(tzinfo=None)

        # Show ALL attendance records for today
        return {
            'type': 'ir.actions.act_window',
            'name': _("Today's Attendance - %s") % self.name,
            'res_model': 'hr.attendance',
            'view_mode': 'list,form',
            'domain': [
                ('check_in', '>=', start_utc),
                ('check_in', '<=', end_utc)
            ],
            'target': 'current',
            'context': {'search_default_group_by_employee': 0},
        }
    
    def download_all_attendance(self, start_date=None, end_date=None):
        """Download attendance immediately for an optional date range
        (called from the wizard) and open the resulting attendance records."""
        self.ensure_one()

        if start_date and end_date:
            self.message_post(
                body=_("Step 1/5: Testing connection to device... (Range: %s to %s)")
                % (start_date, end_date)
            )
        else:
            self.message_post(body=_("Step 1/5: Testing connection to device..."))

        self.test_connection()

        self.message_post(body=_("Step 2/5: Fetching attendance events. This may take a while..."))
        events = self.fetch_all_attendance(start_date=start_date, end_date=end_date)
        self.message_post(body=_("Step 3/5: Fetched %s event(s). Syncing employees...") % len(events))
        self.fetch_employees()
        self.env.cr.commit()

        self.message_post(body=_("Step 4/5: Processing events in batches..."))
        created_ids, updated_ids, skipped_count = self._process_attendance_events_bulk(events)

        self.message_post(
            body=_("Step 5/5: Done. Processed %s event(s) — Created %s, Updated %s, Skipped %s.")
            % (len(events), len(created_ids), len(updated_ids), skipped_count)
        )

        domain = []
        if start_date and end_date:
            user_tz = self.env.user.tz or "UTC"
            local_tz = pytz.timezone(user_tz)
            start_dt_local = local_tz.localize(datetime.combine(start_date, dt_time.min))
            end_dt_local = local_tz.localize(datetime.combine(end_date, dt_time.max))
            start_utc = start_dt_local.astimezone(pytz.UTC).replace(tzinfo=None)
            end_utc = end_dt_local.astimezone(pytz.UTC).replace(tzinfo=None)
            domain = [('check_in', '>=', start_utc), ('check_in', '<=', end_utc)]

        return {
            'type': 'ir.actions.act_window',
            'name': _('All Attendance - %s') % self.name,
            'res_model': 'hr.attendance',
            'view_mode': 'list,form',
            'domain': domain,
            'target': 'current',
        }    
    # Option 2: Show attendance from the last 2 years (more practical)
    # two_years_ago = datetime.now(pytz.UTC) - timedelta(days=730)
    # return {
    #     'type': 'ir.actions.act_window',
    #     'name': _('All Attendance - %s') % self.name,
    #     'res_model': 'hr.attendance',
    #     'view_mode': 'list,form',
    #     'domain': [('check_in', '>=', two_years_ago.strftime('%Y-%m-%d %H:%M:%S'))],
    #     'target': 'current',
    # }
    def _process_attendance_events(self, events):
        """Process a flat list of AcsEvent dicts (today's-attendance flow).
        Returns (created_ids, updated_ids, skipped_count)."""
        self.ensure_one()
        created_ids = []
        updated_ids = []
        skipped_count = 0
    
        for event in events:
            emp_no = event.get("employeeNoString")
            pass_time_str = event.get("time")
            attendance_status = event.get("attendanceStatus")
    
            if not emp_no or not pass_time_str or attendance_status is None:
                continue
    
            employee = self.env["hr.employee"].search(
                [("hikvision_number", "=", emp_no)], limit=1
            )
            if not employee:
                continue
    
            try:
                pass_time = datetime.strptime(pass_time_str, "%Y-%m-%dT%H:%M:%S%z")
                pass_time = pass_time.astimezone(pytz.UTC).replace(tzinfo=None)
            except ValueError:
                continue
    
            if pass_time < employee.create_date.replace(tzinfo=None):
                skipped_count += 1
                continue
    
            if attendance_status == "checkIn":
                same_day_attendance = self.env["hr.attendance"].search([
                    ("employee_id", "=", employee.id),
                    ("check_in", ">=", pass_time.replace(hour=0, minute=0, second=0, microsecond=0)),
                    ("check_in", "<=", pass_time.replace(hour=23, minute=59, second=59, microsecond=999999)),
                ], order="check_in desc", limit=1)
    
                last_attendance = self.env["hr.attendance"].search(
                    [("employee_id", "=", employee.id)],
                    order="check_in desc",
                    limit=1,
                )
    
                if same_day_attendance and not same_day_attendance.check_out:
                    skipped_count += 1
                    continue
    
                if same_day_attendance and same_day_attendance.check_out:
                    if pass_time > same_day_attendance.check_out:
                        new_rec = self.env["hr.attendance"].sudo().create({
                            "employee_id": employee.id,
                            "check_in": pass_time,
                        })
                        created_ids.append(new_rec.id)
                        continue
                    else:
                        skipped_count += 1
                        continue
    
                user_tz = self.env.user.tz or "UTC"
                local_tz = pytz.timezone(user_tz)
    
                if last_attendance and not last_attendance.check_out:
                    checkin_date_local = last_attendance.check_in.astimezone(local_tz).date()
                    end_of_day_local = datetime.combine(checkin_date_local, dt_time(23, 59, 59))
                    end_of_day_local = local_tz.localize(end_of_day_local)
                    end_of_day_utc = end_of_day_local.astimezone(pytz.UTC).replace(tzinfo=None)
    
                    last_attendance.sudo().write({"check_out": end_of_day_utc})
                    updated_ids.append(last_attendance.id)
                    self.env.invalidate_all()
    
                if last_attendance and not last_attendance.check_out and pass_time > last_attendance.check_in:
                    safe_checkout = pass_time - timedelta(seconds=1)
                    last_attendance.sudo().write({"check_out": safe_checkout})
                    if last_attendance.id not in updated_ids:
                        updated_ids.append(last_attendance.id)
    
                try:
                    new_rec = self.env["hr.attendance"].sudo().create({
                        "employee_id": employee.id,
                        "check_in": pass_time,
                    })
                    created_ids.append(new_rec.id)
                except ValidationError:
                    open_att = self.env["hr.attendance"].search([
                        ("employee_id", "=", employee.id),
                        ("check_out", "=", False)
                    ], order="check_in desc", limit=1)
                    if open_att and pass_time > open_att.check_in:
                        open_att.sudo().write({"check_out": pass_time - timedelta(seconds=1)})
                        updated_ids.append(open_att.id)
                        new_rec = self.env["hr.attendance"].sudo().create({
                            "employee_id": employee.id,
                            "check_in": pass_time,
                        })
                        created_ids.append(new_rec.id)
                    else:
                        raise
    
            elif attendance_status == "checkOut":
                same_day_attendance = self.env["hr.attendance"].search([
                    ("employee_id", "=", employee.id),
                    ("check_in", ">=", pass_time.replace(hour=0, minute=0, second=0, microsecond=0)),
                    ("check_in", "<=", pass_time.replace(hour=23, minute=59, second=59, microsecond=999999)),
                ], order="check_in desc", limit=1)

                if same_day_attendance:
                    if pass_time > same_day_attendance.check_in:
                        if not same_day_attendance.check_out or pass_time > same_day_attendance.check_out:
                            same_day_attendance.sudo().write({"check_out": pass_time})
                            updated_ids.append(same_day_attendance.id)
                        else:
                            skipped_count += 1
                    else:
                        skipped_count += 1
                else:
                    new_rec = self.env["hr.attendance"].sudo().create({
                        "employee_id": employee.id,
                        "check_in": pass_time,
                        "check_out": pass_time + timedelta(seconds=1),
                    })
                    created_ids.append(new_rec.id)
    
        return created_ids, updated_ids, skipped_count
    
    
    # ── replaces job_download_all_attendance --------------------------------------
    def _process_attendance_events_bulk(self, events):
        """Process a large list of AcsEvent dicts in chunks, posting a chatter
        progress update after every chunk (this is the 'step by step update'
        replacement for the old job.set_progress calls).
        Returns (created_ids, updated_ids, skipped_count)."""
        self.ensure_one()
        created_ids = []
        updated_ids = []
        skipped_count = 0
    
        chunk_size = 50
        total = len(events)
    
        for chunk_idx in range(0, total, chunk_size):
            chunk_events = events[chunk_idx:chunk_idx + chunk_size]
    
            for event in chunk_events:
                emp_no = event.get("employeeNoString")
                pass_time_str = event.get("time")
                attendance_status = event.get("attendanceStatus")
                inferred_status = False
    
                if not emp_no or not pass_time_str:
                    skipped_count += 1
                    continue
    
                if attendance_status is None:
                    minor = event.get("minor")
                    if minor in [75, 38, 181]:
                        attendance_status = "checkIn"
                        inferred_status = True
                    else:
                        skipped_count += 1
                        continue
    
                employee = self.env["hr.employee"].search(
                    [("hikvision_number", "=", emp_no)], limit=1
                )
                if not employee:
                    skipped_count += 1
                    continue
    
                try:
                    pass_time = datetime.strptime(pass_time_str, "%Y-%m-%dT%H:%M:%S%z")
                    pass_time = pass_time.astimezone(pytz.UTC).replace(tzinfo=None)
                except ValueError:
                    skipped_count += 1
                    continue
    
                if pass_time < employee.create_date.replace(tzinfo=None):
                    skipped_count += 1
                    continue
    
                existing_attendance = self.env["hr.attendance"].search([
                    ("employee_id", "=", employee.id),
                    "|",
                    ("check_in", "=", pass_time),
                    ("check_out", "=", pass_time)
                ], limit=1)
    
                if existing_attendance:
                    skipped_count += 1
                    continue
    
                if attendance_status == "checkIn":
                    same_day_attendance = self.env["hr.attendance"].search([
                        ("employee_id", "=", employee.id),
                        ("check_in", ">=", pass_time.replace(hour=0, minute=0, second=0, microsecond=0)),
                        ("check_in", "<=", pass_time.replace(hour=23, minute=59, second=59, microsecond=999999)),
                    ], order="check_in desc", limit=1)
    
                    last_attendance = self.env["hr.attendance"].search(
                        [("employee_id", "=", employee.id)],
                        order="check_in desc",
                        limit=1,
                    )
    
                    if same_day_attendance and not same_day_attendance.check_out:
                        if inferred_status and pass_time > same_day_attendance.check_in:
                            same_day_attendance.sudo().write({"check_out": pass_time})
                            updated_ids.append(same_day_attendance.id)
                            continue
                        skipped_count += 1
                        continue
    
                    if same_day_attendance and same_day_attendance.check_out:
                        if pass_time > same_day_attendance.check_out:
                            new_rec = self.env["hr.attendance"].sudo().create({
                                "employee_id": employee.id,
                                "check_in": pass_time,
                            })
                            created_ids.append(new_rec.id)
                            continue
                        else:
                            skipped_count += 1
                            continue
    
                    user_tz = self.env.user.tz or "UTC"
                    local_tz = pytz.timezone(user_tz)
    
                    if last_attendance and not last_attendance.check_out:
                        checkin_date_local = last_attendance.check_in.astimezone(local_tz).date()
                        end_of_day_local = datetime.combine(checkin_date_local, dt_time(23, 59, 59))
                        end_of_day_local = local_tz.localize(end_of_day_local)
                        end_of_day_utc = end_of_day_local.astimezone(pytz.UTC).replace(tzinfo=None)
    
                        last_attendance.sudo().write({"check_out": end_of_day_utc})
                        updated_ids.append(last_attendance.id)
    
                    if last_attendance and not last_attendance.check_out and pass_time > last_attendance.check_in:
                        safe_checkout = pass_time - timedelta(seconds=1)
                        last_attendance.sudo().write({"check_out": safe_checkout})
                        if last_attendance.id not in updated_ids:
                            updated_ids.append(last_attendance.id)
    
                    try:
                        new_rec = self.env["hr.attendance"].sudo().create({
                            "employee_id": employee.id,
                            "check_in": pass_time,
                        })
                        created_ids.append(new_rec.id)
                    except ValidationError:
                        open_att = self.env["hr.attendance"].search([
                            ("employee_id", "=", employee.id),
                            ("check_out", "=", False)
                        ], order="check_in desc", limit=1)
                        if open_att and pass_time > open_att.check_in:
                            open_att.sudo().write({"check_out": pass_time - timedelta(seconds=1)})
                            updated_ids.append(open_att.id)
                            new_rec = self.env["hr.attendance"].sudo().create({
                                "employee_id": employee.id,
                                "check_in": pass_time,
                            })
                            created_ids.append(new_rec.id)
                        else:
                            raise
    
                elif attendance_status == "checkOut":
                    same_day_attendance = self.env["hr.attendance"].search([
                        ("employee_id", "=", employee.id),
                        ("check_in", ">=", pass_time.replace(hour=0, minute=0, second=0, microsecond=0)),
                        ("check_in", "<=", pass_time.replace(hour=23, minute=59, second=59, microsecond=999999)),
                    ], order="check_in desc", limit=1)

                    if same_day_attendance:
                        if pass_time > same_day_attendance.check_in:
                            if not same_day_attendance.check_out or pass_time > same_day_attendance.check_out:
                                same_day_attendance.sudo().write({"check_out": pass_time})
                                updated_ids.append(same_day_attendance.id)
                            else:
                                skipped_count += 1
                        else:
                            skipped_count += 1
                    else:
                        new_rec = self.env["hr.attendance"].sudo().create({
                            "employee_id": employee.id,
                            "check_in": pass_time,
                            "check_out": pass_time + timedelta(seconds=1),
                        })
                        created_ids.append(new_rec.id)
            # commit + chatter progress update after every chunk
            try:
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                continue
    
            done = min(chunk_idx + chunk_size, total)
            percent = int(done * 100 / total) if total else 100
            self.message_post(
                body=_("Progress: %s / %s events processed (%s%%). Created so far: %s, Updated so far: %s.")
                % (done, total, percent, len(created_ids), len(updated_ids))
            )
            time_module.sleep(0.1)
    
        return created_ids, updated_ids, skipped_count
    
    

    def fetch_employees(self):
        """Fetch employees from device and sync with Odoo."""
        for device in self:
            url, auth, headers = self._get_api_config("/ISAPI/AccessControl/UserInfo/Search?format=json")

            payload = {
                "UserInfoSearchCond": {
                    "searchID": "1",
                    "searchResultPosition": 0,
                    "maxResults": 50
                }
            }
            fetched_emp_ids = []
            try:
                response = requests.post(url, auth=auth, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    employees = data.get("UserInfoSearch", {}).get("UserInfo", [])
                    for emp in employees:
                        emp_no = emp.get("employeeNo")
                        emp_name = emp.get("name")
                        if not emp_no:
                            continue
                        existing_emp = self.env["hr.employee"].search([("hikvision_number", "=", emp_no)], limit=1)
                        if existing_emp:
                            existing_emp.write({
                                "name": emp_name or existing_emp.name
                            })
                            fetched_emp_ids.append(existing_emp.id)
                        else:
                            new_emp = self.env["hr.employee"].create({
                                "name": emp_name or "Unknown",
                                "hikvision_number": emp_no
                            })
                            fetched_emp_ids.append(new_emp.id)
                    self.env.cr.commit()
                    return {
                        "type": "ir.actions.act_window",
                        "name": _("Fetched Employees"),
                        "res_model": "hr.employee",
                        "view_mode": "list,form",
                        "domain": [("id", "in", fetched_emp_ids)],
                    }
            except requests.exceptions.RequestException:
                pass

    def fetch_logs(self):
        """Fetch and store attendance logs."""
        events = self.fetch_attendance()

        minor_to_attendance_type = {
            38: '1',
            75: '15',
            181: '3',
        }
        status_to_punch_type = {
            'checkIn': '0',
            'checkOut': '1',
            'breakOut': '2',
            'breakIn': '3',
            'overtimeIn': '4',
            'overtimeOut': '5',
            'duplicate': '255',
        }

        for event in events:
            emp_no = event.get("employeeNoString")
            if not emp_no:
                continue

            emp = self.env['hr.employee'].search([('hikvision_number', '=', emp_no)], limit=1)
            if not emp:
                continue

            punch_time_str = event.get("time")
            if not punch_time_str:
                continue
            try:
                normalized = punch_time_str.replace('Z', '+00:00')
                punch_dt = datetime.fromisoformat(normalized)
                punch_dt = punch_dt.astimezone(pytz.UTC).replace(tzinfo=None)

                if punch_dt < emp.create_date.replace(tzinfo=None):
                    continue

            except Exception:
                try:
                    punch_dt = datetime.strptime(punch_time_str[:19], '%Y-%m-%dT%H:%M:%S')
                except Exception:
                    continue

            minor_raw = event.get("minor")
            try:
                minor_val = int(minor_raw) if minor_raw is not None else None
            except (ValueError, TypeError):
                minor_val = None

            attendance_type = minor_to_attendance_type.get(minor_val, '255')
            punch_type = status_to_punch_type.get(event.get("attendanceStatus"), '255')

            existing_log = self.env['hikvision.logs'].search([
                ('employee_id', '=', emp.id),
                ('punching_time', '=', punch_dt),
                ('punch_type', '=', punch_type),
                ('attendance_type', '=', attendance_type),
            ], limit=1)

            if not existing_log:
                self.env['hikvision.logs'].sudo().create({
                    'date': punch_dt.date(),
                    'employee_id': emp.id,
                    'punch_type': punch_type,
                    'attendance_type': attendance_type,
                    'punching_time': punch_dt,
                })

    def set_time(self):
        """Set device time to system time."""
        now = datetime.now()
        offset_minutes = -int((datetime.utcnow() - now).total_seconds() / 60)
        sign = "+" if offset_minutes >= 0 else "-"
        tz_hours = str(abs(offset_minutes) // 60).zfill(2)
        tz_minutes = str(abs(offset_minutes) % 60).zfill(2)

        local_time_str = now.strftime(f"%Y-%m-%dT%H:%M:%S{sign}{tz_hours}:{tz_minutes}")

        xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Time xmlns="http://www.hikvision.com/ver10/XMLSchema">
        <timeMode>manual</timeMode>
        <localTime>{local_time_str}</localTime>
    </Time>
    """

        url = f"http://{self.ip_address}/ISAPI/System/time"
        auth = HTTPDigestAuth(self.username, self.password)

        response = requests.put(
            url,
            auth=auth,
            headers={"Content-Type": "application/xml"},
            data=xml_payload
        )

        if response.status_code == 200:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Successfully Set the Time',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise UserError(_("Please Check the Connection"))

    def _get_next_hikvision_employee_no(self):
        """Get next available employee number."""
        url, auth, headers = self._get_api_config("/ISAPI/AccessControl/UserInfo/Search?format=json")

        payload = {
            "UserInfoSearchCond": {
                "searchID": "1",
                "maxResults": 1000,
                "searchResultPosition": 0
            }
        }

        used_numbers = set()
        try:
            resp = requests.post(url, auth=auth, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                user_list = data.get("UserInfoSearch", {}).get("UserInfo", [])
                for user in user_list:
                    try:
                        num = int(user.get("employeeNo"))
                        used_numbers.add(num)
                    except (ValueError, TypeError):
                        continue
        except Exception:
            pass

        all_odoo_employees = self.env["hr.employee"].with_context(active_test=False).search([
            ("hikvision_number", "!=", False)
        ])

        for emp in all_odoo_employees:
            try:
                num = int(emp.hikvision_number)
                used_numbers.add(num)
            except (ValueError, TypeError):
                continue

        if used_numbers:
            max_no = max(used_numbers)
            next_no = max_no + 1
        else:
            next_no = 1

        return next_no

    def create_hikvision_user(self, employee):
        """Create user on Hikvision device."""
        new_employee_no = self._get_next_hikvision_employee_no()

        employee.hikvision_number = new_employee_no
        self.env.cr.commit()

        url, auth, headers = self._get_api_config("/ISAPI/AccessControl/UserInfo/Record?format=json")

        payload = {
            "UserInfo": {
                "employeeNo": str(new_employee_no),
                "name": employee.name,
                "userType": "normal",
                "valid": {
                    "enable": True,
                    "beginTime": "2020-01-01T00:00:00",
                    "endTime": "2030-01-01T23:59:59"
                },
                "doorRight": "1",
                "RightPlan": [{
                    "doorNo": 1,
                    "planTemplateNo": "1"
                }],
                "faceURL": ""
            }
        }

        response = requests.post(url, auth=auth, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('User created successfully on Hikvision device with ID: %s') % new_employee_no,
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            employee.hikvision_number = False
            self.env.cr.commit()
            raise UserError(_("Failed to create user: %s") % response.text)

    def update_hikvision_user(self, employee):
        """Update user on Hikvision device."""
        if not employee.hikvision_number:
            raise UserError(_("This employee does not have a Hikvision number."))

        url, auth, headers = self._get_api_config("/ISAPI/AccessControl/UserInfo/Modify?format=json")

        payload = {
            "UserInfo": {
                "employeeNo": employee.hikvision_number,
                "name": employee.name,
                "userType": "normal",
                "valid": {
                    "enable": True,
                    "beginTime": "2020-01-01T00:00:00",
                    "endTime": "2030-01-01T23:59:59"
                },
                "doorRight": "1",
                "RightPlan": [{
                    "doorNo": 1,
                    "planTemplateNo": "1"
                }],
                "faceURL": ""
            }
        }

        response = requests.put(url, auth=auth, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('User updated successfully on Hikvision device.'),
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise UserError(_("Failed to update user: %s") % response.text)

    def archive_hikvision_user(self, employee):
        """Delete user from Hikvision device when archived."""
        if not employee.hikvision_number:
            raise UserError(_("This employee does not have a Hikvision number."))

        url, auth, headers = self._get_api_config("/ISAPI/AccessControl/UserInfo/Delete?format=json")

        payload = {
            "UserInfoDelCond": {
                "EmployeeNoList": [
                    {
                        "employeeNo": employee.hikvision_number
                    }
                ]
            }
        }

        try:
            response = requests.put(url, auth=auth, json=payload, headers=headers, timeout=10)
        except requests.RequestException as e:
            raise UserError(_("Connection error: %s") % e)

        if response.status_code in (200, 201):
            employee.active = False
            self.env.cr.commit()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _(
                        'User deleted from device successfully. ID %s preserved in Odoo.') % employee.hikvision_number,
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise UserError(_("Failed to delete user from device: %s") % response.text)

    def delete_hikvision_user(self, employee):
        """Delete user from Hikvision device."""
        return self.archive_hikvision_user(employee)

    @api.model
    def cron_download_attendance_all_devices(self):
        """Cron job to download attendance from all devices daily."""
        devices = self.search([])

        success_count = 0
        error_count = 0

        for device in devices:
            try:
                device.fetch_and_create_attendance()
                success_count += 1
                time_module.sleep(2)
            except Exception:
                error_count += 1
                continue

        return True
