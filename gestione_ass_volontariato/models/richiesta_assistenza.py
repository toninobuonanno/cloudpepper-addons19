# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VolontariatoRichiestaAssistenza(models.Model):
    _name = 'volontariato.richiesta.assistenza'
    _description = 'Richiesta di Assistenza'
    _order = 'data_richiesta desc'
    _rec_name = 'codice'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    codice = fields.Char(
        string='Codice', required=True, copy=False, readonly=True,
        default=lambda self: 'Nuovo',
    )
    state = fields.Selection(
        [
            ('draft', 'Bozza'),
            ('confirmed', 'Confermata'),
            ('accepted', 'Accettata'),
            ('refused', 'Respinta'),
        ],
        string='Stato', default='draft', required=True, copy=False,
        tracking=True,
    )
    data_richiesta = fields.Date(
        string='Data Richiesta', required=True, default=fields.Date.context_today,
    )

    # ───────── Richiedente ─────────
    richiedente_nome_cognome = fields.Char(string='Nome e Cognome', required=True)
    richiedente_data_nascita = fields.Date(string='Data di Nascita')
    richiedente_citta_nascita = fields.Char(string='Città di Nascita')
    richiedente_citta_residenza = fields.Char(string='Città di Residenza')
    richiedente_indirizzo_residenza = fields.Char(string='Indirizzo di Residenza')
    richiedente_provincia_residenza = fields.Char(string='Provincia di Residenza')
    richiedente_telefono = fields.Char(string='Telefono')
    richiedente_email = fields.Char(string='Email')
    richiedente_organizzazione = fields.Char(
        string="In Rappresentanza di Organizzazione/Ente/Associazione",
    )

    # ───────── Richiesta ─────────
    manifestazione = fields.Char(string='Manifestazione', required=True)
    data_da = fields.Date(string='Data Da', required=True)
    data_a = fields.Date(string='Data A', required=True)
    ora_da = fields.Float(string='Dalle Ore')
    ora_a = fields.Float(string='Alle Ore')
    indirizzo_manifestazione = fields.Char(string='Indirizzo Manifestazione')
    citta_manifestazione = fields.Char(string='Città Manifestazione')

    presenza_medico = fields.Boolean(string='Presenza Medico')
    medico_nome_cognome = fields.Char(string='Nome e Cognome Medico')
    medico_fornito_da = fields.Selection(
        [
            ('richiedente', 'Dal Richiedente'),
            ('associazione', "Dall'Associazione"),
        ],
        string='Medico Fornito da',
    )

    note = fields.Text(string='Note')

    # ───────── Validazioni ─────────
    @api.constrains('data_da', 'data_a')
    def _check_date(self):
        for record in self:
            if record.data_da and record.data_a and record.data_a < record.data_da:
                raise ValidationError(
                    'La data di fine manifestazione non può essere antecedente alla data di inizio.'
                )

    @api.constrains('presenza_medico', 'medico_nome_cognome', 'medico_fornito_da')
    def _check_medico(self):
        for record in self:
            if record.presenza_medico and not (record.medico_nome_cognome and record.medico_fornito_da):
                raise ValidationError(
                    'In presenza del medico è necessario indicare nome, cognome e da chi viene fornito.'
                )

    @api.onchange('presenza_medico')
    def _onchange_presenza_medico(self):
        if not self.presenza_medico:
            self.medico_nome_cognome = False
            self.medico_fornito_da = False

    # ───────── Workflow ─────────
    def action_confirm(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(
                    'Solo le richieste in stato Bozza possono essere confermate.'
                )
            record.state = 'confirmed'

    def action_accept(self):
        for record in self:
            if record.state != 'confirmed':
                raise ValidationError(
                    'Solo le richieste confermate possono essere accettate.'
                )
            record.state = 'accepted'

    def action_refuse(self):
        for record in self:
            if record.state != 'confirmed':
                raise ValidationError(
                    'Solo le richieste confermate possono essere respinte.'
                )
            record.state = 'refused'

    def action_set_draft(self):
        for record in self:
            record.state = 'draft'

    # ───────── Numerazione automatica ─────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('codice', 'Nuovo') == 'Nuovo':
                vals['codice'] = self.env['ir.sequence'].next_by_code(
                    'volontariato.richiesta.assistenza'
                ) or 'Nuovo'
        return super().create(vals_list)
