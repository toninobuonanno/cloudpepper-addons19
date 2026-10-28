# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Separa anche la numerazione di Donazioni/Prestiti Presidi tra le
    company esistenti (vedi gestione_ass_volontariato/migrations/
    19.0.2.16.0/post-migration.py per i codici del modulo principale).
    Rieseguibile senza effetti collaterali: le sequenze già create non
    vengono duplicate.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    for company in env['res.company'].search([]):
        company._volontariato_setup_sequenze()
