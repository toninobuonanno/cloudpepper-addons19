# -*- coding: utf-8 -*-
from odoo import models

SEQUENZE_VOLONTARIATO = [
    ('volontariato.intervento', 'Numerazione Interventi', 'INT-', 4),
    ('volontariato.esercitazione', 'Numerazione Esercitazioni', 'ESE-', 4),
    ('volontariato.turno', 'Numerazione Turni', 'TUR-', 4),
    ('volontariato.richiesta.assistenza', 'Numerazione Richieste di Assistenza', 'RA-', 4),
]


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _volontariato_sequenze_da_separare(self):
        """Elenco (code, name, prefix, padding) delle numerazioni da rendere
        indipendenti per company. Estendibile dai moduli dipendenti (es.
        Prestito Presidi) tramite super()."""
        return list(SEQUENZE_VOLONTARIATO)

    def _volontariato_setup_sequenze(self):
        """Crea (se mancante) una ir.sequence dedicata a questa company per
        ciascuna numerazione del modulo Volontariato, così che il contatore
        non sia più condiviso tra le company. Per la company più vecchia
        (quella con id più basso) il contatore riparte da dove era arrivata
        la sequenza condivisa, per non duplicare codici già assegnati;
        per le altre company riparte da 1. Rieseguibile senza effetti
        collaterali."""
        self.ensure_one()
        Sequence = self.env['ir.sequence']
        main_company = self.env['res.company'].search([], order='id asc', limit=1)
        for code, name, prefix, padding in self._volontariato_sequenze_da_separare():
            existing = Sequence.search([
                ('code', '=', code),
                ('company_id', '=', self.id),
            ], limit=1)
            if existing:
                continue
            number_next = 1
            if self.id == main_company.id:
                shared = Sequence.search([
                    ('code', '=', code),
                    ('company_id', '=', False),
                ], limit=1)
                if shared:
                    number_next = shared.number_next_actual
            Sequence.create({
                'name': '%s (%s)' % (name, self.name),
                'code': code,
                'prefix': prefix,
                'padding': padding,
                'company_id': self.id,
                'number_next': number_next,
            })

    def action_volontariato_setup_sequenze(self):
        for company in self:
            company._volontariato_setup_sequenze()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Numerazioni Volontariato',
                'message': 'Numerazioni separate configurate per %s.' % ', '.join(self.mapped('name')),
                'type': 'success',
            },
        }
