# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta
import pytz
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

    calendar_event_id = fields.Many2one(
        'calendar.event', string='Evento Calendario', copy=False,
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

    def action_add_to_calendar(self):
        self.ensure_one()
        CalendarEvent = self.env['calendar.event']
        categ = self.env.ref('gestione_ass_volontariato.calendar_event_type_esercitazione', raise_if_not_found=False)

        user_tz = pytz.timezone(self.env.user.tz or 'UTC')

        start_naive = datetime.combine(self.data, time()) + timedelta(hours=self.ora_inizio)
        stop_naive = datetime.combine(self.data, time()) + timedelta(hours=(self.ora_fine or self.ora_inizio + 1))

        start = user_tz.localize(start_naive).astimezone(pytz.utc).replace(tzinfo=None)
        stop = user_tz.localize(stop_naive).astimezone(pytz.utc).replace(tzinfo=None)

        descrizione = 'Esercitazione %s\nTipologia: %s\nDescrizione: %s\nPartecipanti: %s' % (
            self.codice,
            self.tipo_id.name or 'Non specificata',
            self.descrizione or 'Nessuna',
            ', '.join(self.partecipante_ids.mapped('name')) or 'Nessuno',
        )

        if self.calendar_event_id:
            self.calendar_event_id.write({
                'name': '%s - %s' % (self.tipo_id.name or 'Esercitazione', self.descrizione or ''),
                'start': start,
                'stop': stop,
                'description': descrizione,
            })
            event = self.calendar_event_id
        else:
            vals = {
                'name': '%s - %s' % (self.tipo_id.name or 'Esercitazione', self.descrizione or ''),
                'start': start,
                'stop': stop,
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
                    'volontariato.esercitazione'
                ) or 'Nuovo'
        return super().create(vals_list)
