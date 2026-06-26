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
    ruolo_id = fields.Many2one(
        'volontariato.ruolo', string='Ruolo', required=True,
        default=lambda self: self.env.ref('gestione_ass_volontariato.ruolo_volontario', raise_if_not_found=False),
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Volontario', required=True,
    )
    data_intervento = fields.Date(
        related='intervento_id.data', string='Data Intervento', store=True,
    )

    display_name_squadra = fields.Char(
        string='Descrizione', compute='_compute_display_name_squadra',
    )

    def _compute_display_name_squadra(self):
        for record in self:
            nome_ruolo = record.ruolo_id.name or ''
            nome_persona = record.employee_id.name or ''
            record.display_name_squadra = f'{nome_ruolo}: {nome_persona}' if nome_persona else nome_ruolo
