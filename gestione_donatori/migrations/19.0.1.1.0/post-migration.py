# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Ricalcola per sicurezza il campo 'Soggetto' (name), diventato un
    campo calcolato da Cognome+Nome, nel caso l'aggiornamento non lo abbia
    già ricalcolato per tutti i donatori esistenti."""
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    donatori = env['donatori.donatore'].with_context(active_test=False).search([])
    env.add_to_compute(donatori._fields['name'], donatori)
