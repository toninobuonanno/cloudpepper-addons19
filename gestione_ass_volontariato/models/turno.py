# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta
import pytz
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
    tipo_intervento_id = fields.Many2one(
        'volontariato.tipo.intervento', string='Tipo Intervento',
        default=lambda self: self.env.ref(
            'gestione_ass_volontariato.tipo_intervento_emergenza',
            raise_if_not_found=False,
        ),
    )
    luogo = fields.Char(string='Luogo')
    data = fields.Date(string='Data', required=True, default=fields.Date.context_today)
    ora_inizio = fields.Float(string='Ora Inizio', required=True)
    ora_fine = fields.Float(string='Ora Fine')
    durata_ore = fields.Float(
        string='Durata (ore)', compute='_compute_durata_ore', store=True,
    )
    note = fields.Text(string='Note')

    calendar_event_id = fields.Many2one(
        'calendar.event', string='Evento Calendario', copy=False,
    )

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

    def action_add_to_calendar(self):
        self.ensure_one()
        CalendarEvent = self.env['calendar.event']
        categ = self.env.ref('gestione_ass_volontariato.calendar_event_type_turno', raise_if_not_found=False)

        user_tz = pytz.timezone(self.env.user.tz or 'UTC')

        start_naive = datetime.combine(self.data, time()) + timedelta(hours=self.ora_inizio)
        stop_naive = datetime.combine(self.data, time()) + timedelta(hours=(self.ora_fine or self.ora_inizio + 1))

        start = user_tz.localize(start_naive).astimezone(pytz.utc).replace(tzinfo=None)
        stop = user_tz.localize(stop_naive).astimezone(pytz.utc).replace(tzinfo=None)

        tipo_label = self.tipo_intervento_id.name or ''
        titolo = '%s%s' % (self.evento, ' (%s)' % tipo_label if tipo_label else '')

        descrizione = 'Turno %s\nTipo Intervento: %s\nPartecipanti: %s' % (
            self.codice,
            tipo_label or 'Non specificato',
            ', '.join(self.squadra_ids.mapped('employee_id.name')) or 'Nessuno',
        )

        if self.calendar_event_id:
            self.calendar_event_id.write({
                'name': titolo,
                'start': start,
                'stop': stop,
                'location': self.luogo or '',
                'description': descrizione,
            })
            event = self.calendar_event_id
        else:
            vals = {
                'name': titolo,
                'start': start,
                'stop': stop,
                'location': self.luogo or '',
                'description': descrizione,
            }
            if categ:
                vals['categ_ids'] = [(6, 0, [categ.id])]
            event = CalendarEvent.create(vals)
            self.calendar_event_id = event

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'calendar.event',
            'res_id': event.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('codice', 'Nuovo') == 'Nuovo':
                vals['codice'] = self.env['ir.sequence'].next_by_code(
                    'volontariato.turno'
                ) or 'Nuovo'
        return super().create(vals_list)
