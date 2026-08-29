# -*- coding: utf-8 -*-
from odoo import models, fields


class TdcPort(models.Model):
    _name = 'tdc.port'
    _description = 'Port (Loading / Discharge)'
    _order = 'name'

    name = fields.Char(string='Port (City, Country)', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This port already exists.'),
    ]


class TdcVessel(models.Model):
    _name = 'tdc.vessel'
    _description = 'Ocean Vessel / Flight'
    _order = 'name'

    name = fields.Char(string='Ocean Vessel / Flight Name', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This vessel/flight already exists.'),
    ]


class TdcIgmTerminal(models.Model):
    _name = 'tdc.igm.terminal'
    _description = 'IGM Collectorate / Terminal'
    _order = 'name'

    name = fields.Char(string='IGM Collectorate/Terminal', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This IGM collectorate/terminal already exists.'),
    ]


class TdcCustomsCollectorate(models.Model):
    _name = 'tdc.customs.collectorate'
    _description = 'Customs Collectorate'
    _order = 'name'

    name = fields.Char(string='Customs Collectorate', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This customs collectorate already exists.'),
    ]
