# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class VolontariatoPrimaNotaWizard(models.TransientModel):
    _name = 'volontariato.prima.nota.wizard'
    _description = 'Nuovo Movimento Prima Nota'

    tipo = fields.Selection(
        [('entrata', 'Entrata'), ('uscita', 'Uscita')],
        string='Tipo', required=True, default='entrata',
    )
    data = fields.Date(
        string='Data', required=True, default=fields.Date.context_today,
    )
    importo = fields.Monetary(
        string='Importo', required=True, currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id,
    )
    journal_id = fields.Many2one(
        'account.journal', string='Cassa / Banca', required=True,
        domain="[('type', 'in', ('cash', 'bank')), ('company_id', '=', company_id)]",
    )
    conto_natura_id = fields.Many2one(
        'account.account', string='Natura (conto)', required=True,
        domain="[('account_type', 'in', tipo == 'entrata' and "
               "('income', 'income_other') or "
               "('expense', 'expense_direct_cost')), "
               "('company_ids', 'in', company_id)]",
    )
    analitica_id = fields.Many2one(
        'account.analytic.account', string='Destinazione (Mod. D)',
        required=True,
        domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]",
    )
    partner_id = fields.Many2one('res.partner', string='Da / A')
    descrizione = fields.Char(string='Descrizione', required=True)
    intervento_id = fields.Many2one(
        'volontariato.intervento', string='Intervento Collegato',
    )
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True,
    )

    @api.onchange('tipo')
    def _onchange_tipo(self):
        self.conto_natura_id = False

    def action_registra(self):
        self.ensure_one()
        if self.importo <= 0:
            raise UserError(_("L'importo deve essere maggiore di zero."))

        liquidita = self.journal_id.default_account_id
        if not liquidita:
            raise UserError(_(
                'Il giornale %s non ha un conto di default configurato. '
                'Eseguire "Configura contabilità ETS" dal menu '
                'Configurazione.') % self.journal_id.name)

        if self.tipo == 'entrata':
            line_liq = {'account_id': liquidita.id,
                        'debit': self.importo, 'credit': 0.0}
            line_nat = {'account_id': self.conto_natura_id.id,
                        'debit': 0.0, 'credit': self.importo}
        else:
            line_nat = {'account_id': self.conto_natura_id.id,
                        'debit': self.importo, 'credit': 0.0}
            line_liq = {'account_id': liquidita.id,
                        'debit': 0.0, 'credit': self.importo}

        common = {
            'partner_id': self.partner_id.id or False,
            'name': self.descrizione,
        }
        line_nat.update(common)
        line_nat.update({
            'analytic_distribution': {str(self.analitica_id.id): 100},
            'volontariato_analitica_id': self.analitica_id.id,
        })
        line_liq.update(common)

        move = self.env['account.move'].with_company(self.company_id).create({
            'move_type': 'entry',
            'journal_id': self.journal_id.id,
            'date': self.data,
            'ref': self.descrizione,
            'partner_id': self.partner_id.id or False,
            'volontariato_intervento_id': self.intervento_id.id or False,
            'line_ids': [(0, 0, line_liq), (0, 0, line_nat)],
        })
        move.action_post()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Movimento registrato'),
                'message': '%s · %s € · %s' % (
                    dict(self._fields['tipo'].selection)[self.tipo],
                    f'{self.importo:.2f}',
                    self.descrizione,
                ),
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
