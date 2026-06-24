# -*- coding: utf-8 -*-
from odoo import fields, models


class VolontariatoTipoCertAttrezzatura(models.Model):
    _name = 'volontariato.tipo.cert.attrezzatura'
    _description = 'Tipo Certificazione Attrezzatura'
    _order = 'name'

    name = fields.Char(string='Nome', required=True, help='Es. Revisione, Collaudo, Taratura...')
    active = fields.Boolean(string='Attivo', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Questo tipo di certificazione esiste già.'),
    ]
