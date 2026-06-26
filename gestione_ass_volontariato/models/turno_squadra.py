# -*- coding: utf-8 -*-
from odoo import fields, models


class VolontariatoTurnoSquadra(models.Model):
    _name = 'volontariato.turno.squadra'
    _description = 'Partecipante Turno'
    _order = 'sequence, id'

    turno_id = fields.Many2one(
        'volontariato.turno', string='Turno',
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
    qualifica_id = fields.Many2one(
        related='employee_id.volontariato_qualifica_id',
        string='Qualifica', readonly=True, store=True,
    )

    data = fields.Date(
        related='turno_id.data', string='Data', readonly=True, store=True,
    )
    evento = fields.Char(
        related='turno_id.evento', string='Evento', readonly=True, store=True,
    )
    luogo = fields.Char(
        related='turno_id.luogo', string='Luogo', readonly=True, store=True,
    )
    ora_inizio = fields.Float(
        related='turno_id.ora_inizio', string='Ora Inizio', readonly=True, store=True,
    )
    ora_fine = fields.Float(
        related='turno_id.ora_fine', string='Ora Fine', readonly=True, store=True,
    )
    durata_ore = fields.Float(
        related='turno_id.durata_ore', string='Durata (ore)', readonly=True, store=True,
    )
