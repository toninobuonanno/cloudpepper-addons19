# -*- coding: utf-8 -*-
from odoo import fields, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    company_id = fields.Many2one(
        'res.company', string='Sede',
        help='Impostato automaticamente solo sugli eventi generati da '
             'Turni/Esercitazioni Volontariato per separarli tra le sedi '
             '(company). Lasciato vuoto (nessuna restrizione) per tutti '
             'gli altri eventi di calendario.',
    )
