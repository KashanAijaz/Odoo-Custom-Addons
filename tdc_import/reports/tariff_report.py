# -*- coding: utf-8 -*-
from odoo import models


class TdcImportTariffReport(models.AbstractModel):
    _name = 'report.tdc_import.report_tariff_document'
    _description = 'Import GD Tariff PDF Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['tdc.import.tariff'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'tdc.import.tariff',
            'docs': docs,
        }
