# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    fbr_api_url = fields.Char(
        string="FBR DI API URL",
        default="https://gw.fbr.gov.pk/di_data/v1/di/postinvoicedata_sb",
        help="Use Sandbox or Production URL for FBR Digital Invoicing API."
    )
    fbr_security_token = fields.Char(
        string="FBR Security Token",
        help="Security Token provided by FBR Portal (e.fbr.gov.pk)."
    )
    fbr_cookie_string = fields.Text(
        string="FBR Cookie String",
        help="Copy full Cookie header string from working cURL/Postman (JSESSIONID, cookiesession1, etc.)."
    )
    fbr_sandbox_mode = fields.Boolean(
        string="Use Sandbox",
        default=True,
        help="Enable to use Sandbox URL instead of Production."
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        IrConfig = self.env['ir.config_parameter'].sudo()
        res.update(
            fbr_api_url=IrConfig.get_param(
                'l10n_pk_fbr.api_url',
                default="https://gw.fbr.gov.pk/di_data/v1/di/postinvoicedata_sb"
            ),
            fbr_security_token=IrConfig.get_param('l10n_pk_fbr.security_token', default=""),
            fbr_cookie_string=IrConfig.get_param('l10n_pk_fbr.cookie_string', default=""),
            fbr_sandbox_mode=IrConfig.get_param('l10n_pk_fbr.sandbox_mode', default='True') == 'True',
        )
        return res

    def set_values(self):
        super().set_values()
        IrConfig = self.env['ir.config_parameter'].sudo()
        IrConfig.set_param('l10n_pk_fbr.api_url', self.fbr_api_url or "")
        IrConfig.set_param('l10n_pk_fbr.security_token', self.fbr_security_token or "")
        IrConfig.set_param('l10n_pk_fbr.cookie_string', self.fbr_cookie_string or "")
        IrConfig.set_param('l10n_pk_fbr.sandbox_mode', str(bool(self.fbr_sandbox_mode)))
