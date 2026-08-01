# -*- coding: utf-8 -*-
from odoo import fields, models


class DonatoriParametro(models.Model):
    _name = 'donatori.parametro'
    _description = 'Parametro Donatore'
    _order = 'data_donazione desc, cognome, nome'

    active = fields.Boolean(string='Attivo', default=True)

    donatore_id = fields.Many2one(
        'donatori.donatore', string='Donatore', required=True, ondelete='restrict',
    )
    data_donazione = fields.Date(
        string='Data Donazione', required=True, default=fields.Date.context_today,
    )
    cognome = fields.Char(related='donatore_id.cognome', string='Cognome', store=True, readonly=True)
    nome = fields.Char(related='donatore_id.nome', string='Nome', store=True, readonly=True)
    luogo_nascita = fields.Char(related='donatore_id.comune_nascita', string='Nato a', store=True, readonly=True)
    data_nascita = fields.Date(related='donatore_id.data_nascita', string='Data Nascita', store=True, readonly=True)

    peso = fields.Float(string='Peso (kg)')
    pressione_arteriosa = fields.Char(string='PA', help='Es. 120/75')
    frequenza_cardiaca = fields.Integer(string='FC')
    emoglobina = fields.Float(string='HGB', digits=(16, 1))
    idoneo = fields.Selection(
        [('si', 'Sì'), ('no', 'No')], string='Idoneo',
    )
    altri_parametri = fields.Char(string='Altri Parametri')
    note = fields.Html(string='Note', sanitize_style=True)
