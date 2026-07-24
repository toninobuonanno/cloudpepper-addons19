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

    # prefetch=False: questi campi custom non esistono sul modello ridotto
    # hr.employee.public. Se restassero nel gruppo di prefetch di default,
    # verrebbero caricati "in blocco" insieme a qualsiasi altro campo di
    # hr.employee (es. da res.partner.get_attendee_detail nel Calendario),
    # e per un utente senza accesso HR completo Odoo blocca l'intera
    # richiesta con un AccessError. Restano comunque leggibili/scrivibili
    # normalmente quando richiesti esplicitamente dalle nostre viste.
    volontariato_codice_fiscale = fields.Char(
        string='Codice Fiscale', size=16,
        help='Codice fiscale del volontario',
        prefetch=False,
    )
    volontariato_provincia_nascita_id = fields.Many2one(
        'res.country.state', string='Provincia di Nascita',
        domain="[('country_id.code', '=', 'IT')]",
        help='Provincia italiana di nascita. Necessaria per calcolare '
             'correttamente il codice fiscale quando più comuni hanno '
             'lo stesso nome in province diverse.',
        prefetch=False,
    )
    volontariato_data_iscrizione = fields.Date(
        string='Data Iscrizione',
        help="Data di iscrizione del volontario all'associazione",
        prefetch=False,
    )
    volontariato_data_accettazione = fields.Date(
        string='Data Accettazione',
        help="Data di accettazione della domanda di iscrizione",
        prefetch=False,
    )
    volontariato_qualifica_id = fields.Many2one(
        'volontariato.qualifica',
        string='Qualifica Volontario',
        help='Qualifica operativa del volontario (es. Soccorritore, Autista Soccorritore...)',
        prefetch=False,
    )
    volontariato_nr_primis = fields.Char(
        string='Nr. Primis',
        help='Numero identificativo Primis del volontario',
        prefetch=False,
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
