# -*- coding: utf-8 -*-
from odoo import api, fields, models


class VolontariatoCertificazioneVolontario(models.Model):
    _name = 'volontariato.certificazione.volontario'
    _description = 'Certificazione Volontario'
    _order = 'data_scadenza'

    employee_id = fields.Many2one(
        'hr.employee', string='Volontario', required=True, ondelete='cascade',
    )
    tipo_cert_id = fields.Many2one(
        'volontariato.tipo.cert.volontario', string='Tipo Certificazione', required=True,
    )
    data_conseguimento = fields.Date(string='Data Conseguimento')
    data_scadenza = fields.Date(string='Data Scadenza')

    stato_scadenza = fields.Selection(
        [
            ('ok', 'Valida'),
            ('warn', 'In scadenza'),
            ('expired', 'Scaduta'),
            ('none', 'Senza scadenza'),
        ],
        string='Stato',
        compute='_compute_stato_scadenza',
        store=True,
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

    @api.model
    def _cron_aggiorna_stati_scadenza(self):
        """Ricalcola lo stato scadenza di tutte le certificazioni.
        Necessario perché il campo è 'store=True' e altrimenti non si
        aggiornerebbe automaticamente con il solo passare dei giorni."""
        records = self.search([])
        records._compute_stato_scadenza()
