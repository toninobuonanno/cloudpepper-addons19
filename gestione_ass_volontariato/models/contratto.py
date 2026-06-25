# -*- coding: utf-8 -*-
from odoo import api, fields, models


class VolontariatoContratto(models.Model):
    _name = 'volontariato.contratto'
    _description = 'Contratto / Assicurazione Generale'
    _order = 'data_scadenza'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    tipo_id = fields.Many2one(
        'volontariato.tipo.contratto', string='Tipo Contratto', required=True,
    )
    fornitore = fields.Char(string='Fornitore / Compagnia')
    numero_contratto = fields.Char(string='N° Contratto / Polizza')
    periodicita = fields.Selection(
        [
            ('mensile', 'Mensile'),
            ('trimestrale', 'Trimestrale'),
            ('semestrale', 'Semestrale'),
            ('annuale', 'Annuale'),
            ('biennale', 'Biennale'),
            ('una_tantum', 'Una Tantum'),
        ],
        string='Periodicità',
    )
    data_contratto = fields.Date(string='Data Contratto')
    data_scadenza = fields.Date(string='Scadenza')
    importo = fields.Float(string='Importo (€)')
    note = fields.Text(string='Note')
    active = fields.Boolean(string='Attivo', default=True)

    rata_ids = fields.One2many(
        'volontariato.contratto.rata', 'contratto_id', string='Rate / Pagamenti',
    )

    totale_pagato = fields.Float(
        string='Totale Pagato', compute='_compute_totali', store=True,
    )
    totale_in_attesa = fields.Float(
        string='Totale in Attesa', compute='_compute_totali', store=True,
    )

    stato_scadenza = fields.Selection(
        [
            ('ok', 'Valida'),
            ('warn', 'In scadenza'),
            ('expired', 'Scaduta'),
            ('none', 'Senza scadenza'),
        ],
        string='Stato',
        compute='_compute_stato_scadenza',
    )

    @api.depends('rata_ids.importo', 'rata_ids.pagato')
    def _compute_totali(self):
        for record in self:
            record.totale_pagato = sum(
                r.importo for r in record.rata_ids if r.pagato
            )
            record.totale_in_attesa = sum(
                r.importo for r in record.rata_ids if not r.pagato
            )

    @api.depends('data_scadenza')
    def _compute_stato_scadenza(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.data_scadenza:
                record.stato_scadenza = 'none'
            elif record.data_scadenza < today:
                record.stato_scadenza = 'expired'
            elif (record.data_scadenza - today).days <= 30:
                record.stato_scadenza = 'warn'
            else:
                record.stato_scadenza = 'ok'
