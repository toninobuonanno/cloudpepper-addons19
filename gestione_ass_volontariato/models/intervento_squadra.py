# -*- coding: utf-8 -*-
from odoo import fields, models


class VolontariatoInterventoSquadra(models.Model):
    _name = 'volontariato.intervento.squadra'
    _description = 'Membro Squadra Intervento'
    _order = 'sequence, id'

    intervento_id = fields.Many2one(
        'volontariato.intervento', string='Intervento',
        required=True, ondelete='cascade',
    )
    sequence = fields.Integer(string='Sequenza', default=10)
    ruolo = fields.Selection(
        [
            ('caposquadra', 'Caposquadra'),
            ('autista', 'Autista'),
            ('volontario', 'Volontario'),
        ],
        string='Ruolo', required=True, default='volontario',
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Volontario', required=True,
    )

    # Comodo per liste raggruppate o stampe: nome leggibile del ruolo + persona
    display_name_squadra = fields.Char(
        string='Descrizione', compute='_compute_display_name_squadra',
    )

    def _compute_display_name_squadra(self):
        ruoli = dict(self._fields['ruolo'].selection)
        for record in self:
            nome_ruolo = ruoli.get(record.ruolo, '')
            nome_persona = record.employee_id.name or ''
            record.display_name_squadra = f'{nome_ruolo}: {nome_persona}' if nome_persona else nome_ruolo
