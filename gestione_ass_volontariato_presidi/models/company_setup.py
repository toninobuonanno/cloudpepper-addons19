# -*- coding: utf-8 -*-
from odoo import models

SEQUENZE_PRESIDI = [
    ('volontariato.presidio.donazione', 'Numerazione Donazioni Presidi', 'DON-', 4),
    ('volontariato.presidio.prestito', 'Numerazione Prestiti Presidi', 'PST-', 4),
]


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _volontariato_sequenze_da_separare(self):
        return super()._volontariato_sequenze_da_separare() + list(SEQUENZE_PRESIDI)
