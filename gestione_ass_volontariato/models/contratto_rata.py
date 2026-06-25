# -*- coding: utf-8 -*-
from odoo import api, fields, models


class VolontariatoContrattoRata(models.Model):
    _name = 'volontariato.contratto.rata'
    _description = 'Rata / Pagamento Contratto'
    _order = 'scadenza'

    contratto_id = fields.Many2one(
        'volontariato.contratto', string='Contratto',
        required=True, ondelete='cascade',
    )
    data_rata = fields.Date(string='Data Rata')
    importo = fields.Float(string='Importo (€)')
    scadenza = fields.Date(string='Scadenza')
    pagato = fields.Boolean(string='Pagato')
    note = fields.Char(string='Note')

    stato_scadenza = fields.Selection(
        [
            ('paid', 'Pagata'),
            ('ok', 'Da pagare'),
            ('warn', 'In scadenza'),
            ('expired', 'Scaduta'),
            ('none', 'Senza scadenza'),
        ],
        string='Stato',
        compute='_compute_stato_scadenza',
        store=True,
    )

    @api.depends('pagato', 'scadenza')
    def _compute_stato_scadenza(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.pagato:
                record.stato_scadenza = 'paid'
            elif not record.scadenza:
                record.stato_scadenza = 'none'
            elif record.scadenza < today:
                record.stato_scadenza = 'expired'
            elif (record.scadenza - today).days <= 30:
                record.stato_scadenza = 'warn'
            else:
                record.stato_scadenza = 'ok'

    @api.model
    def _cron_aggiorna_stati_scadenza(self):
        records = self.search([])
        records._compute_stato_scadenza()
