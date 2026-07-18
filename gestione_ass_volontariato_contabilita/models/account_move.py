# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    volontariato_intervento_id = fields.Many2one(
        'volontariato.intervento', string='Intervento Collegato',
        index=True, copy=False,
    )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Destinazione esplicita (oltre alla analytic_distribution nativa):
    # rende la dashboard e il rendiconto semplici e raggruppabili.
    volontariato_analitica_id = fields.Many2one(
        'account.analytic.account', string='Destinazione',
        index=True, copy=False,
    )
    volontariato_sezione_id = fields.Many2one(
        related='volontariato_analitica_id.sezione_rendiconto_id',
        string='Sezione Mod. D', store=True,
    )
    volontariato_tipo = fields.Selection(
        [('entrata', 'Entrata'), ('uscita', 'Uscita')],
        string='Tipo', compute='_compute_volontariato_tipo', store=True,
    )
    volontariato_importo = fields.Monetary(
        string='Importo', compute='_compute_volontariato_tipo', store=True,
        currency_field='company_currency_id',
    )
    volontariato_entrata = fields.Monetary(
        string='Entrate', compute='_compute_volontariato_tipo', store=True,
        currency_field='company_currency_id',
    )
    volontariato_uscita = fields.Monetary(
        string='Uscite', compute='_compute_volontariato_tipo', store=True,
        currency_field='company_currency_id',
    )

    @api.depends('account_id.account_type', 'debit', 'credit')
    def _compute_volontariato_tipo(self):
        for line in self:
            acc_type = line.account_id.account_type
            if acc_type in ('income', 'income_other'):
                line.volontariato_tipo = 'entrata'
                line.volontariato_importo = line.credit - line.debit
                line.volontariato_entrata = line.credit - line.debit
                line.volontariato_uscita = 0.0
            elif acc_type in ('expense', 'expense_depreciation',
                              'expense_direct_cost'):
                line.volontariato_tipo = 'uscita'
                line.volontariato_importo = line.debit - line.credit
                line.volontariato_entrata = 0.0
                line.volontariato_uscita = line.debit - line.credit
            else:
                line.volontariato_tipo = False
                line.volontariato_importo = 0.0
                line.volontariato_entrata = 0.0
                line.volontariato_uscita = 0.0
