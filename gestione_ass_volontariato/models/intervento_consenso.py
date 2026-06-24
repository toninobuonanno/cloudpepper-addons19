# -*- coding: utf-8 -*-
from odoo import fields, models


class VolontariatoInterventoConsenso(models.Model):
    _name = 'volontariato.intervento.consenso'
    _description = 'Consensi Intervento'

    intervento_id = fields.Many2one(
        'volontariato.intervento', string='Intervento',
        required=True, ondelete='cascade',
    )
    consenso_fornito = fields.Boolean(string='Ha Fornito il Consenso')
    rifiuto_ricovero = fields.Boolean(string='Rifiuto Ricovero')
