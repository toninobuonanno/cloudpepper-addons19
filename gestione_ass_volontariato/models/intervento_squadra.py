# -*- coding: utf-8 -*-
from odoo import fields, models


class VolontariatoInterventoSquadra(models.Model):
    _name = 'volontariato.intervento.squadra'
    _description = 'Membro Squadra Intervento'
    _order = 'sequence, id'

    intervento_id = fields.Many2one(
        'volontariato.intervento', string='Intervento',
        required=True, ondelete='cascade',
    )
    sequence = fields.Integer(string='Sequenza', default=10)
    ruolo_id = fields.Many2one(
        'volontariato.ruolo', string='Ruolo', required=True,
        default=lambda self: self.env.ref('gestione_ass_volontariato.ruolo_volontario', raise_if_not_found=False),
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Volontario', required=True,
    )
    data_intervento = fields.Date(
        related='intervento_id.data', string='Data Intervento', store=True,
    )

    # ── Campi related dall'intervento: colonne per la Dashboard Volontari ──
    codice_intervento = fields.Char(
        related='intervento_id.codice', string='Codice Intervento', store=True,
    )
    state = fields.Selection(
        related='intervento_id.state', string='Stato', store=True,
    )
    tipo_intervento_id = fields.Many2one(
        related='intervento_id.tipo_intervento_id',
        string='Tipo Intervento', store=True,
    )
    vehicle_id = fields.Many2one(
        related='intervento_id.vehicle_id', string='Automezzo', store=True,
    )
    richiedente_id = fields.Many2one(
        related='intervento_id.richiedente_id',
        string='Richiesto da', store=True,
    )
    luogo = fields.Char(
        related='intervento_id.luogo', string="Luogo dell'Intervento",
    )
    luogo_citta = fields.Char(
        related='intervento_id.luogo_citta', string='Città',
    )
    luogo_destinazione = fields.Char(
        related='intervento_id.luogo_destinazione', string='Destinazione',
    )
    ora_inizio = fields.Float(
        related='intervento_id.ora_inizio', string='Ora Inizio',
    )
    ora_fine = fields.Float(
        related='intervento_id.ora_fine', string='Ora Fine',
    )
    durata_ore = fields.Float(
        related='intervento_id.durata_ore', string='Durata (ore)', store=True,
    )
    km_totali = fields.Integer(
        related='intervento_id.km_totali', string='Km Totali', store=True,
    )

    display_name_squadra = fields.Char(
        string='Descrizione', compute='_compute_display_name_squadra',
    )

    def _compute_display_name_squadra(self):
        for record in self:
            nome_ruolo = record.ruolo_id.name or ''
            nome_persona = record.employee_id.name or ''
            record.display_name_squadra = f'{nome_ruolo}: {nome_persona}' if nome_persona else nome_ruolo
