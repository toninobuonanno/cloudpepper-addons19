# -*- coding: utf-8 -*-
from odoo import fields, models


class VolontariatoSezioneRendiconto(models.Model):
    _name = 'volontariato.sezione.rendiconto'
    _description = 'Sezione Rendiconto per Cassa (Mod. D)'
    _order = 'sequence, code'

    code = fields.Char(string='Lettera', required=True, size=2)
    name = fields.Char(string='Descrizione', required=True)
    sequence = fields.Integer(string='Sequenza', default=10)
    active = fields.Boolean(string='Attiva', default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Esiste già una sezione con questa lettera.'),
    ]

    def _compute_display_name(self):
        for record in self:
            record.display_name = f'{record.code} · {record.name}'
