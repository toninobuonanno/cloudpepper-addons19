# -*- coding: utf-8 -*-
from odoo import fields, models


class VolontariatoInterventoPaziente(models.Model):
    _name = 'volontariato.intervento.paziente'
    _description = 'Dati Anagrafici Paziente'

    intervento_id = fields.Many2one(
        'volontariato.intervento', string='Intervento',
        required=True, ondelete='cascade',
    )
    cognome_nome = fields.Char(string='Cognome e Nome')
    nato_a = fields.Char(string='Nato/a a')
    nato_il = fields.Date(string='Il (data di nascita)')
    residente_a = fields.Char(string='Residente a')
    indirizzo = fields.Char(string='Indirizzo')
    professione = fields.Char(string='Professione')
    sospetta_diagnosi = fields.Char(string='Sospetta Diagnosi')
    causato_da = fields.Char(string='Causato da')
