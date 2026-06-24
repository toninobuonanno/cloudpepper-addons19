# -*- coding: utf-8 -*-
from odoo import fields, models


class VolontariatoTipoContratto(models.Model):
    _name = 'volontariato.tipo.contratto'
    _description = 'Tipo Contratto / Assicurazione'
    _order = 'name'

    name = fields.Char(
        string='Nome', required=True,
        help='Es. Assicurazione RC, Assicurazione Infortuni, Contratto Ossigeno...'
    )
    active = fields.Boolean(string='Attivo', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Questo tipo di contratto esiste già.'),
    ]
