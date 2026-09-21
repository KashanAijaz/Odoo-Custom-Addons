# -*- coding: utf-8 -*-
import json
import logging
import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    fbr_synced = fields.Boolean(string="Synced with FBR", default=False)
    fbr_response = fields.Text(string="FBR Response", readonly=True)

    def action_sync_with_fbr(self):
        """
        Called when user clicks 'Sync with FBR' button.
        Sends invoice data to FBR API.
        """
        for move in self:
            if move.move_type not in ("out_invoice", "out_refund"):
                raise UserError("Only Customer Invoices and Credit Notes can be synced with FBR.")

            payload = move._prepare_fbr_payload()
            _logger.info("FBR Payload for Invoice %s:\n%s", move.name, json.dumps(payload, indent=2))

            response = move._call_fbr_api(payload)

            move.fbr_response = json.dumps(response, indent=2)
            if "error" in response or "fault" in response:
                raise UserError(f"FBR returned an error: {response}")

            move.fbr_synced = True
            move.message_post(
                body=f"✅ Invoice synced with FBR.<br/>Response:<br/><pre>{json.dumps(response, indent=2)}</pre>")

    # -------------------------------------------------------------------------
    # Payload Preparation
    # -------------------------------------------------------------------------
    def _prepare_fbr_payload(self):
        """Map Odoo invoice to FBR JSON structure. If you want ot add more fields, please add in items and payload"""
        self.ensure_one()

        buyer = self.partner_id

        items = []
        for line in self.invoice_line_ids:
            rate = line.tax_ids[0].amount if line.tax_ids else 0
            line_tax_total = (line.price_subtotal * rate) / 100

            items.append({
                "hsCode": line.product_id.hs_code or "6002.9000",
                "productDescription": line.product_id.name or "Unknown",

                "uoM": line.product_id.hs_unit_measure or "KG",
                "quantity": line.quantity or 1,
                "totalValues": line.price_total or 0,
                "valueSalesExcludingST": line.price_subtotal or 0,
                "fixedNotifiedValueOrRetailPrice": 0,
                "rate": f"{rate}%",
                "salesTaxApplicable": line_tax_total or 0,
                "salesTaxWithheldAtSource": 0,
                "extraTax": "",
                "furtherTax": 0,
                "sroScheduleNo": "",
                "fedPayable": 0,
                "discount": line.discount or 0,
                "saleType": "Processing/Conversion of Goods",
                "sroItemSerialNo": ""
            })

        payload = {
            "invoiceType": "Sale Invoice",
            "invoiceDate": (self.invoice_date or fields.Date.today()).strftime("%Y-%m-%d"),
            "sellerNTNCNIC": self.company_id.vat or "1234567",
            "sellerBusinessName": self.company_id.name or 'Unknown',
            "sellerProvince": self.company_id.state_id.name if self.company_id.state_id else "Punjab",
            "sellerAddress": self.company_id.street or "Address",

            "buyerNTNCNIC": buyer.vat or "",
            "buyerBusinessName": buyer.name or 'Anonymous',
            "buyerProvince": buyer.state_id.name if buyer.state_id else "Punjab",
            "buyerAddress": buyer.street or "Address",
            "buyerRegistrationType": "Registered" if buyer.vat else "Unregistered",

            "invoiceRefNo": self.name or "",
            "scenarioId": "SN016",
            "items": items
        }

        return payload

    # -------------------------------------------------------------------------
    # API Call
    # -------------------------------------------------------------------------
    def _call_fbr_api(self, payload):
        """Perform API call to FBR."""
        IrConfig = self.env["ir.config_parameter"].sudo()
        api_url = IrConfig.get_param(
            "l10n_pk_fbr.api_url",
            default="https://gw.fbr.gov.pk/di_data/v1/di/postinvoicedata_sb"
        )
        token = IrConfig.get_param("l10n_pk_fbr.security_token")
        cookie_string = IrConfig.get_param("l10n_pk_fbr.cookie_string")

        if not token:
            raise UserError("FBR Security Token is not configured. Please set it in Settings.")
        if not cookie_string:
            raise UserError("FBR Cookie is missing. Please set it in Settings.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "Cookie": cookie_string,
        }

        try:
            response = requests.post(
                api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=60,
                verify=False  # ⚠️ disable only in sandbox, not in production
            )
            _logger.info("FBR Response [%s]: %s", response.status_code, response.text)

            try:
                return response.json()
            except Exception:
                return {"error": response.text}

        except requests.RequestException as e:
            _logger.exception("FBR API call failed")
            return {"error": str(e)}
