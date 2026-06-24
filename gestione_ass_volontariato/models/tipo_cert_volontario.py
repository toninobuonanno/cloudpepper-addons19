# -*- coding: utf-8 -*-
from odoo import fields, models


class VolontariatoTipoCertVolontario(models.Model):
    _name = 'volontariato.tipo.cert.volontario'
    _description = 'Tipo Certificazione Volontario'
    _order = 'name'

    name = fields.Char(string='Nome', required=True, help='Es. BLS, BLS-D, PBLSD...')
    active = fields.Boolean(string='Attivo', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Questo tipo di certificazione esiste già.'),
    ]
