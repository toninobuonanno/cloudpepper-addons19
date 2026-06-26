# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VolontariatoTurno(models.Model):
    _name = 'volontariato.turno'
    _description = 'Turno Volontari'
    _order = 'data, ora_inizio'
    _rec_name = 'codice'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    codice = fields.Char(
        string='Codice', required=True, copy=False, readonly=True,
        default=lambda self: 'Nuovo',
    )

    evento = fields.Char(string='Evento', required=True, help="Es. Calcetto / Volley, Assistenza Parrocchia...")
    luogo = fields.Char(string='Luogo')
    data = fields.Date(string='Data', required=True, default=fields.Date.context_today)
    ora_inizio = fields.Float(string='Ora Inizio', required=True)
    ora_fine = fields.Float(string='Ora Fine')
    durata_ore = fields.Float(
        string='Durata (ore)', compute='_compute_durata_ore', store=True,
    )
    note = fields.Text(string='Note')

    squadra_ids = fields.One2many(
        'volontariato.turno.squadra', 'turno_id', string='Volontari Partecipanti',
    )
    numero_partecipanti = fields.Integer(
        string='Numero Partecipanti', compute='_compute_numero_partecipanti', store=True,
    )

    stato_completo = fields.Selection(
        [
            ('completo', 'Completo'),
            ('parziale', 'Da Completare'),
            ('vuoto', 'Nessun Volontario'),
        ],
        string='Stato', compute='_compute_stato_completo', store=True,
    )

    @api.depends('ora_inizio', 'ora_fine')
    def _compute_durata_ore(self):
        for record in self:
            if record.ora_fine and record.ora_inizio is not None:
                diff = record.ora_fine - record.ora_inizio
                record.durata_ore = diff if diff >= 0 else diff + 24
            else:
                record.durata_ore = 0

    @api.depends('squadra_ids')
    def _compute_numero_partecipanti(self):
        for record in self:
            record.numero_partecipanti = len(record.squadra_ids)

    @api.depends('squadra_ids')
    def _compute_stato_completo(self):
        for record in self:
            if not record.squadra_ids:
                record.stato_completo = 'vuoto'
            elif len(record.squadra_ids) < 2:
                record.stato_completo = 'parziale'
            else:
                record.stato_completo = 'completo'

    @api.constrains('squadra_ids')
    def _check_ruolo_responsabile_unico(self):
        for record in self:
            ruoli_responsabili = record.squadra_ids.filtered(lambda r: r.ruolo_id.is_responsabile).mapped('ruolo_id')
            for ruolo in ruoli_responsabili:
                membri = record.squadra_ids.filtered(lambda r: r.ruolo_id == ruolo)
                if len(membri) > 1:
                    raise ValidationError(
                        'Non è possibile assegnare più di un "%s" allo stesso turno.' % ruolo.name
                    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('codice', 'Nuovo') == 'Nuovo':
                vals['codice'] = self.env['ir.sequence'].next_by_code(
                    'volontariato.turno'
                ) or 'Nuovo'
        return super().create(vals_list)
