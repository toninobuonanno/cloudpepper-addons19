# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Separa la numerazione tra le company esistenti: crea per ciascuna
    (compresa quella originale, che continua dal numero già raggiunto)
    una ir.sequence dedicata per ogni codice del modulo Volontariato,
    così che non condividano più lo stesso contatore. Chiama lo stesso
    metodo usato dalla voce di menu "Configura Numerazioni per questa
    Sede", quindi è rieseguibile senza effetti collaterali.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    for company in env['res.company'].search([]):
        company._volontariato_setup_sequenze()
