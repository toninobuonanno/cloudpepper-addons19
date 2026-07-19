# -*- coding: utf-8 -*-
from odoo import api, fields, models


class VolontariatoPresidio(models.Model):
    _name = 'volontariato.presidio'
    _description = 'Presidio Sanitario'
    _order = 'name'

    name = fields.Char(string='Presidio', required=True)
    categoria = fields.Selection(
        [
            ('letto', 'Letto Ortopedico'),
            ('materasso', 'Materasso Antidecubito'),
            ('aspiratore', 'Aspiratore Secreti'),
            ('carrozzina', 'Carrozzina'),
            ('deambulatore', 'Deambulatore / Bastone'),
            ('pannoloni', 'Pannoloni / Materiale di Consumo'),
            ('altro', 'Altro'),
        ],
        string='Categoria', required=True, default='altro',
    )
    consumabile = fields.Boolean(
        string='Materiale di Consumo', default=False,
        help='Il presidio viene ceduto e non rientra a magazzino (es. '
             'pannoloni). Se spuntato non compare tra i presidi in '
             'prestito da restituire.',
    )
    descrizione = fields.Text(string='Descrizione')
    note = fields.Text(string='Note')
    active = fields.Boolean(string='Attivo', default=True)

    donazione_riga_ids = fields.One2many(
        'volontariato.presidio.donazione.riga', 'presidio_id',
        string='Righe Donazione',
    )
    prestito_riga_ids = fields.One2many(
        'volontariato.presidio.prestito.riga', 'presidio_id',
        string='Righe Prestito',
    )

    qty_donata = fields.Float(
        string='Totale Carico', compute='_compute_quantita', store=True,
        help='Quantità totale caricata a magazzino da donazioni confermate.',
    )
    qty_in_prestito = fields.Float(
        string='In Prestito', compute='_compute_quantita', store=True,
        help='Quantità attualmente presso i richiedenti (non ancora rientrata).',
    )
    qty_disponibile = fields.Float(
        string='Disponibile a Magazzino', compute='_compute_quantita', store=True,
    )

    @api.depends(
        'donazione_riga_ids.quantita',
        'donazione_riga_ids.donazione_id.state',
        'prestito_riga_ids.quantita_fornita',
        'prestito_riga_ids.quantita_rientrata',
        'prestito_riga_ids.prestito_id.state',
    )
    def _compute_quantita(self):
        for presidio in self:
            presidio.qty_donata = sum(
                r.quantita for r in presidio.donazione_riga_ids
                if r.donazione_id.state == 'confirmed'
            )
            presidio.qty_in_prestito = sum(
                (r.quantita_fornita - r.quantita_rientrata)
                for r in presidio.prestito_riga_ids
                if r.prestito_id.state == 'confirmed'
            )
            presidio.qty_disponibile = presidio.qty_donata - presidio.qty_in_prestito
