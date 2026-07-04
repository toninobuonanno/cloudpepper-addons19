# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.onchange('volontariato_codice_fiscale')
    def _onchange_volontariato_codice_fiscale(self):
        if self.volontariato_codice_fiscale:
            self.volontariato_codice_fiscale = (
                self.volontariato_codice_fiscale.upper().strip()
            )

    volontariato_codice_fiscale = fields.Char(
        string='Codice Fiscale', size=16,
        help='Codice fiscale del volontario',
    )
    volontariato_data_iscrizione = fields.Date(
        string='Data Iscrizione',
        help="Data di iscrizione del volontario all'associazione",
    )
    volontariato_data_accettazione = fields.Date(
        string='Data Accettazione',
        help="Data di accettazione della domanda di iscrizione",
    )
    volontariato_qualifica_id = fields.Many2one(
        'volontariato.qualifica',
        string='Qualifica Volontario',
        help='Qualifica operativa del volontario (es. Soccorritore, Autista Soccorritore...)',
    )
    volontariato_nr_primis = fields.Char(
        string='Nr. Primis',
        help='Numero identificativo Primis del volontario',
    )
    volontariato_cert_ids = fields.One2many(
        'volontariato.certificazione.volontario',
        'employee_id',
        string='Certificazioni',
    )
    volontariato_cert_count = fields.Integer(
        string='Numero Certificazioni',
        compute='_compute_volontariato_cert_count',
    )

    def _compute_volontariato_cert_count(self):
        for employee in self:
            employee.volontariato_cert_count = len(employee.volontariato_cert_ids)

    def action_open_cf_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Calcola Codice Fiscale',
            'res_model': 'volontariato.codice.fiscale.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }
