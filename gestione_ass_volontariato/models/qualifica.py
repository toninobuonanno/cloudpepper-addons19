# -*- coding: utf-8 -*-
from odoo import fields, models


class VolontariatoQualifica(models.Model):
    _name = 'volontariato.qualifica'
    _description = 'Qualifica Volontario'
    _order = 'name'

    name = fields.Char(string='Nome Qualifica', required=True)
    active = fields.Boolean(string='Attivo', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Questa qualifica esiste già.'),
    ]
