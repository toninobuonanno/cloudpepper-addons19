# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DonatoriParametro(models.Model):
    _name = 'donatori.parametro'
    _description = 'Parametro Donatore'
    _order = 'data_donazione desc, cognome, nome'

    active = fields.Boolean(string='Attivo', default=True)

    donatore_id = fields.Many2one(
        'donatori.donatore', string='Donatore', ondelete='set null',
        help='Donatore anagrafico collegato, se individuato.',
    )
    data_donazione = fields.Date(
        string='Data Donazione', required=True, default=fields.Date.context_today,
    )
    cognome = fields.Char(string='Cognome', required=True)
    nome = fields.Char(string='Nome', required=True)
    luogo_nascita = fields.Char(string='Nato a')
    data_nascita = fields.Date(string='Data Nascita')

    peso = fields.Float(string='Peso (kg)')
    pressione_arteriosa = fields.Char(string='PA', help='Es. 120/75')
    frequenza_cardiaca = fields.Integer(string='FC')
    emoglobina = fields.Float(string='HGB', digits=(16, 1))
    idoneo = fields.Selection(
        [('si', 'Sì'), ('no', 'No')], string='Idoneo',
    )
    altri_parametri = fields.Char(string='Altri Parametri')
    note = fields.Text(string='Note')

    @api.onchange('cognome', 'nome', 'data_nascita')
    def _onchange_ricerca_donatore(self):
        if self.donatore_id or not (self.cognome and self.nome):
            return
        nome_completo = '%s %s' % (self.cognome.strip(), self.nome.strip())
        domain = [('name', '=ilike', nome_completo)]
        if self.data_nascita:
            domain.append(('data_nascita', '=', self.data_nascita))
        donatore = self.env['donatori.donatore'].search(domain, limit=2)
        if len(donatore) == 1:
            self.donatore_id = donatore

    @api.onchange('donatore_id')
    def _onchange_donatore_id(self):
        if not self.donatore_id:
            return
        nome_completo = (self.donatore_id.name or '').strip().split()
        if nome_completo:
            self.cognome = nome_completo[0]
            self.nome = ' '.join(nome_completo[1:])
        self.data_nascita = self.donatore_id.data_nascita
