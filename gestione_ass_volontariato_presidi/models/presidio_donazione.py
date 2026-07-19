# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VolontariatoPresidioDonazione(models.Model):
    _name = 'volontariato.presidio.donazione'
    _description = 'Donazione Presidi (Carico Magazzino)'
    _order = 'data desc'
    _rec_name = 'codice'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    codice = fields.Char(
        string='Codice', required=True, copy=False, readonly=True,
        default=lambda self: 'Nuovo',
    )
    donatore_id = fields.Many2one(
        'res.partner', string='Donatore', required=True,
        tracking=True,
    )
    data = fields.Date(
        string='Data Donazione', required=True,
        default=fields.Date.context_today,
    )
    state = fields.Selection(
        [
            ('draft', 'Bozza'),
            ('confirmed', 'Confermata'),
        ],
        string='Stato', default='draft', required=True, copy=False,
        tracking=True,
    )
    note = fields.Text(string='Note')

    riga_ids = fields.One2many(
        'volontariato.presidio.donazione.riga', 'donazione_id',
        string='Presidi Donati',
    )
    quantita_totale = fields.Float(
        string='Quantità Totale', compute='_compute_quantita_totale', store=True,
    )

    @api.depends('riga_ids.quantita')
    def _compute_quantita_totale(self):
        for record in self:
            record.quantita_totale = sum(record.riga_ids.mapped('quantita'))

    def action_confirm(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(
                    'Solo le donazioni in stato Bozza possono essere confermate.'
                )
            if not record.riga_ids:
                raise ValidationError(
                    'Aggiungere almeno un presidio prima di confermare la donazione.'
                )
            record.state = 'confirmed'

    def action_set_draft(self):
        for record in self:
            record.state = 'draft'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('codice', 'Nuovo') == 'Nuovo':
                vals['codice'] = self.env['ir.sequence'].next_by_code(
                    'volontariato.presidio.donazione'
                ) or 'Nuovo'
        return super().create(vals_list)


class VolontariatoPresidioDonazioneRiga(models.Model):
    _name = 'volontariato.presidio.donazione.riga'
    _description = 'Riga Donazione Presidio'

    donazione_id = fields.Many2one(
        'volontariato.presidio.donazione', string='Donazione',
        required=True, ondelete='cascade',
    )
    donatore_id = fields.Many2one(
        related='donazione_id.donatore_id', string='Donatore', store=True,
    )
    data = fields.Date(related='donazione_id.data', string='Data', store=True)
    presidio_id = fields.Many2one(
        'volontariato.presidio', string='Presidio', required=True,
    )
    quantita = fields.Float(string='Quantità', required=True, default=1.0)
    matricola = fields.Char(
        string='Matricola / N. Identificativo',
        help='Facoltativo: utile per tracciare un pezzo specifico '
             '(es. numero di serie di un letto o di un aspiratore).',
    )
    note = fields.Char(string='Note')
