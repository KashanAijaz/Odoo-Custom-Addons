# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TariffReportAbstract(models.AbstractModel):
    _name = 'report.tdc_import.tariff_report_template'
    _description = 'Tariff Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tariff.import'].browse(docids)
        
        if not docs:
            raise UserError(_("No tariff records found to print."))
        
        return {
            'doc_ids': docids,
            'doc_model': 'tariff.import',
            'docs': docs,
            'data': data,
        }