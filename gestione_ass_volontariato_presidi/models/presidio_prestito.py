# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VolontariatoPresidioPrestito(models.Model):
    _name = 'volontariato.presidio.prestito'
    _description = 'Prestito Presidi'
    _order = 'data_richiesta desc'
    _rec_name = 'codice'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    codice = fields.Char(
        string='Codice', required=True, copy=False, readonly=True,
        default=lambda self: 'Nuovo',
    )
    richiedente_id = fields.Many2one(
        'res.partner', string='Richiedente', required=True,
        tracking=True,
    )
    data_richiesta = fields.Date(
        string='Data Richiesta', required=True,
        default=fields.Date.context_today,
    )
    state = fields.Selection(
        [
            ('draft', 'Bozza'),
            ('confirmed', 'Confermato'),
        ],
        string='Stato', default='draft', required=True, copy=False,
        tracking=True,
    )
    stato_rientro = fields.Selection(
        [
            ('in_corso', 'In Corso'),
            ('parziale', 'Parzialmente Rientrato'),
            ('rientrato', 'Rientrato'),
        ],
        string='Rientro', compute='_compute_stato_rientro', store=True,
        tracking=True,
    )
    note = fields.Text(string='Note')

    riga_ids = fields.One2many(
        'volontariato.presidio.prestito.riga', 'prestito_id',
        string='Presidi Forniti',
    )

    @api.depends('riga_ids.rientrato', 'riga_ids.quantita_fornita', 'riga_ids.quantita_rientrata')
    def _compute_stato_rientro(self):
        for record in self:
            righe = record.riga_ids
            if not righe:
                record.stato_rientro = 'in_corso'
            elif all(r.rientrato for r in righe):
                record.stato_rientro = 'rientrato'
            elif any(r.quantita_rientrata for r in righe):
                record.stato_rientro = 'parziale'
            else:
                record.stato_rientro = 'in_corso'

    def action_confirm(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(
                    'Solo i prestiti in stato Bozza possono essere confermati.'
                )
            if not record.riga_ids:
                raise ValidationError(
                    'Aggiungere almeno un presidio prima di confermare il prestito.'
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
                    'volontariato.presidio.prestito'
                ) or 'Nuovo'
        return super().create(vals_list)


class VolontariatoPresidioPrestitoRiga(models.Model):
    _name = 'volontariato.presidio.prestito.riga'
    _description = 'Riga Prestito Presidio'

    prestito_id = fields.Many2one(
        'volontariato.presidio.prestito', string='Prestito',
        required=True, ondelete='cascade',
    )
    richiedente_id = fields.Many2one(
        related='prestito_id.richiedente_id', string='Richiedente', store=True,
    )
    presidio_id = fields.Many2one(
        'volontariato.presidio', string='Presidio', required=True,
    )
    consumabile = fields.Boolean(related='presidio_id.consumabile', string='Consumabile')

    # ───────── Fornitura (movimento in uscita) ─────────
    quantita_fornita = fields.Float(string='Quantità Fornita', required=True, default=1.0)
    data_fornitura = fields.Date(
        string='Data Fornitura', required=True, default=fields.Date.context_today,
    )
    matricola = fields.Char(
        string='Matricola / N. Identificativo',
        help='Facoltativo: numero di serie del pezzo specifico fornito, '
             'se si vuole tracciare quale esemplare è stato dato.',
    )

    # ───────── Rientro (movimento in entrata) ─────────
    quantita_rientrata = fields.Float(string='Quantità Rientrata', default=0.0)
    data_rientro = fields.Date(
        string='Data Rientro',
        help='Vuoto = il presidio è ancora presso il richiedente.',
    )
    condizione_rientro = fields.Selection(
        [
            ('buono', 'Buono Stato'),
            ('da_igienizzare', 'Da Igienizzare/Sanificare'),
            ('danneggiato', 'Danneggiato/Da Riparare'),
            ('dismesso', 'Da Dismettere'),
        ],
        string='Condizione al Rientro',
    )

    rientrato = fields.Boolean(
        string='Rientrato', compute='_compute_rientrato', store=True,
    )
    note = fields.Char(string='Note')

    @api.depends('quantita_fornita', 'quantita_rientrata', 'data_rientro')
    def _compute_rientrato(self):
        for riga in self:
            riga.rientrato = bool(riga.data_rientro) and (
                riga.quantita_rientrata >= riga.quantita_fornita
            )

    @api.constrains('quantita_fornita', 'quantita_rientrata')
    def _check_quantita(self):
        for riga in self:
            if riga.quantita_fornita <= 0:
                raise ValidationError('La quantità fornita deve essere maggiore di zero.')
            if riga.quantita_rientrata < 0:
                raise ValidationError('La quantità rientrata non può essere negativa.')
            if riga.quantita_rientrata > riga.quantita_fornita:
                raise ValidationError(
                    'La quantità rientrata non può superare la quantità fornita.'
                )

    def action_registra_rientro(self):
        for riga in self:
            riga.write({
                'data_rientro': fields.Date.context_today(riga),
                'quantita_rientrata': riga.quantita_fornita,
            })
