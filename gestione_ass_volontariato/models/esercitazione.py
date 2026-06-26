# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VolontariatoEsercitazione(models.Model):
    _name = 'volontariato.esercitazione'
    _description = 'Esercitazione'
    _order = 'data desc, ora_inizio desc'
    _rec_name = 'codice'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    codice = fields.Char(
        string='Codice', required=True, copy=False, readonly=True,
        default=lambda self: 'Nuovo',
    )

    tipo_id = fields.Many2one(
        'volontariato.tipo.esercitazione', string='Tipologia', required=True,
    )
    data = fields.Date(string='Data', required=True, default=fields.Date.context_today)
    ora_inizio = fields.Float(string='Ora Inizio', required=True)
    ora_fine = fields.Float(string='Ora Fine', required=True)
    durata_ore = fields.Float(
        string='Durata (ore)', compute='_compute_durata_ore', store=True,
    )

    descrizione = fields.Char(string='Descrizione')
    note = fields.Text(string='Note')

    partecipante_ids = fields.Many2many(
        'hr.employee',
        relation='volontariato_esercitazione_employee_rel',
        column1='esercitazione_id',
        column2='employee_id',
        string='Volontari Partecipanti',
    )
    numero_partecipanti = fields.Integer(
        string='Numero Partecipanti', compute='_compute_numero_partecipanti', store=True,
    )

    @api.depends('ora_inizio', 'ora_fine')
    def _compute_durata_ore(self):
        for record in self:
            if record.ora_fine and record.ora_inizio is not None:
                diff = record.ora_fine - record.ora_inizio
                record.durata_ore = diff if diff >= 0 else diff + 24
            else:
                record.durata_ore = 0

    @api.depends('partecipante_ids')
    def _compute_numero_partecipanti(self):
        for record in self:
            record.numero_partecipanti = len(record.partecipante_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('codice', 'Nuovo') == 'Nuovo':
                vals['codice'] = self.env['ir.sequence'].next_by_code(
                    'volontariato.esercitazione'
                ) or 'Nuovo'
        return super().create(vals_list)
