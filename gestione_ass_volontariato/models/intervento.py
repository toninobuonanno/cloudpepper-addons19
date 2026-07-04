# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VolontariatoIntervento(models.Model):
    _name = 'volontariato.intervento'
    _description = 'Intervento (Foglio di Viaggio)'
    _order = 'data desc, ora_inizio desc'
    _rec_name = 'codice'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ───────── Identificazione ─────────
    codice = fields.Char(
        string='Codice', required=True, copy=False, readonly=True,
        default=lambda self: 'Nuovo',
    )
    state = fields.Selection(
        [
            ('draft', 'Bozza'),
            ('confirmed', 'Confermato'),
            ('cancelled', 'Annullato'),
        ],
        string='Stato', default='draft', required=True, copy=False,
        tracking=True,
    )

    # ───────── SEZIONE 1 — Dati Intervento ─────────
    vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Automezzo', required=True,
    )
    tipo_intervento_id = fields.Many2one(
        'volontariato.tipo.intervento', string='Tipo Intervento', required=True,
        default=lambda self: self.env.ref(
            'gestione_ass_volontariato.tipo_intervento_emergenza',
            raise_if_not_found=False,
        ),
    )
    data = fields.Date(string='Data Intervento', required=True, default=fields.Date.context_today)

    ora_inizio = fields.Float(string='Ora Inizio Intervento', required=True)
    ora_fine = fields.Float(string='Ora Fine Intervento', required=True)
    ora_arrivo_luogo = fields.Float(string='Ora Arrivo sul Luogo')
    ora_partenza_luogo = fields.Float(string='Ora Partenza dal Luogo')
    ora_arrivo_dest = fields.Float(string='Ora Arrivo a Destinazione')

    durata_ore = fields.Float(
        string='Durata Totale (ore)', compute='_compute_durata_ore', store=True,
    )

    km_iniziali = fields.Integer(string='Km Iniziali', required=True)
    km_finali = fields.Integer(string='Km Finali', required=True)
    km_totali = fields.Integer(
        string='Km Totali', compute='_compute_km_totali', store=True,
    )

    richiedente_id = fields.Many2one(
        'res.partner', string='Intervento Richiesto da',
    )
    richiedente_citta = fields.Char(
        string='Città Richiedente', related='richiedente_id.city',
        store=True, readonly=True,
    )
    richiedente_provincia = fields.Char(
        string='Provincia Richiedente', related='richiedente_id.state_id.name',
        store=True, readonly=True,
    )

    luogo = fields.Char(string="Luogo dell'Intervento")
    luogo_citta = fields.Char(string='Città')
    luogo_provincia = fields.Char(string='Provincia')
    luogo_destinazione = fields.Char(string='Luogo di Destinazione')

    # Rifornimento
    rifornimento = fields.Boolean(string='Rifornimento Carburante')
    rifornimento_euro = fields.Float(string='Importo Rifornimento (€)')
    rifornimento_litri = fields.Float(string='Litri')

    # Pulizia (solo sì/no)
    pulizia = fields.Boolean(string='Pulizia Post-Intervento')

    # Offerta (con dettagli)
    offerta = fields.Boolean(string='Offerta Ricevuta')
    offerta_euro = fields.Float(string='Importo Offerta (€)')
    offerta_ricevuta = fields.Char(string='Rif. Ricevuta')

    note = fields.Text(string='Modalità di Svolgimento e Annotazioni')

    # ───────── SEZIONE 2 — Squadra ─────────
    squadra_ids = fields.One2many(
        'volontariato.intervento.squadra', 'intervento_id', string='Squadra',
    )
    caposquadra_id = fields.Many2one(
        'hr.employee', string='Caposquadra', compute='_compute_caposquadra_autista',
        store=True,
    )
    autista_id = fields.Many2one(
        'hr.employee', string='Autista', compute='_compute_caposquadra_autista',
        store=True,
    )
    numero_volontari = fields.Integer(
        string='Numero Volontari', compute='_compute_numero_volontari', store=True,
    )

    # ───────── SEZIONE 3 — Paziente ─────────
    paziente_ids = fields.One2many(
        'volontariato.intervento.paziente', 'intervento_id', string='Dati Paziente',
    )

    # ───────── SEZIONE 4 — Consensi ─────────
    consenso_ids = fields.One2many(
        'volontariato.intervento.consenso', 'intervento_id', string='Consensi',
    )

    # ───────── Computed ─────────
    @api.depends('km_iniziali', 'km_finali')
    def _compute_km_totali(self):
        for record in self:
            if record.km_finali and record.km_iniziali:
                record.km_totali = record.km_finali - record.km_iniziali
            else:
                record.km_totali = 0

    @api.depends('ora_inizio', 'ora_fine')
    def _compute_durata_ore(self):
        for record in self:
            if record.ora_fine and record.ora_inizio is not None:
                diff = record.ora_fine - record.ora_inizio
                record.durata_ore = diff if diff >= 0 else diff + 24
            else:
                record.durata_ore = 0

    @api.depends('squadra_ids.ruolo_id', 'squadra_ids.employee_id')
    def _compute_caposquadra_autista(self):
        for record in self:
            capo = record.squadra_ids.filtered(lambda r: r.ruolo_id.name == 'Caposquadra')
            autista = record.squadra_ids.filtered(lambda r: r.ruolo_id.name == 'Autista')
            record.caposquadra_id = capo[:1].employee_id
            record.autista_id = autista[:1].employee_id

    @api.depends('squadra_ids.ruolo_id')
    def _compute_numero_volontari(self):
        for record in self:
            record.numero_volontari = len(
                record.squadra_ids.filtered(lambda r: r.ruolo_id.name == 'Volontario')
            )

    # ───────── Validazioni ─────────
    @api.constrains('km_iniziali', 'km_finali')
    def _check_km(self):
        for record in self:
            if record.km_finali and record.km_iniziali and record.km_finali < record.km_iniziali:
                raise ValidationError(
                    'I km finali non possono essere inferiori ai km iniziali.'
                )

    @api.constrains('squadra_ids')
    def _check_ruolo_responsabile_unico(self):
        for record in self:
            ruoli_responsabili = record.squadra_ids.filtered(lambda r: r.ruolo_id.is_responsabile).mapped('ruolo_id')
            for ruolo in ruoli_responsabili:
                membri = record.squadra_ids.filtered(lambda r: r.ruolo_id == ruolo)
                if len(membri) > 1:
                    raise ValidationError(
                        'Non è possibile assegnare più di un "%s" allo stesso intervento.' % ruolo.name
                    )

    # ───────── Workflow ─────────
    def action_confirm(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(
                    'Solo gli interventi in stato Bozza possono essere confermati.'
                )
            record.state = 'confirmed'

    def action_cancel(self):
        for record in self:
            if record.state == 'cancelled':
                continue
            record.state = 'cancelled'

    def action_set_draft(self):
        for record in self:
            record.state = 'draft'

    # ───────── Numerazione automatica ─────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('codice', 'Nuovo') == 'Nuovo':
                vals['codice'] = self.env['ir.sequence'].next_by_code(
                    'volontariato.intervento'
                ) or 'Nuovo'
        return super().create(vals_list)
