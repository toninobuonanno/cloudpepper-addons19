# -*- coding: utf-8 -*-
from odoo import api, fields, models


class VolontariatoIntervento(models.Model):
    _inherit = 'volontariato.intervento'

    movimento_count = fields.Integer(
        string='Movimenti Contabili', compute='_compute_movimento_count',
    )

    def _compute_movimento_count(self):
        data = self.env['account.move']._read_group(
            [('volontariato_intervento_id', 'in', self.ids)],
            ['volontariato_intervento_id'], ['__count'],
        )
        counts = {rec.id: count for rec, count in data}
        for record in self:
            record.movimento_count = counts.get(record.id, 0)

    def action_registra_offerta(self):
        self.ensure_one()
        conto_offerte = self.env.company._volontariato_get_account('3.01')
        journal = self.env['account.journal'].search([
            ('code', '=', 'PNC'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        analitica = self.env['account.analytic.account'].search([
            ('name', '=', 'Ambulanza'),
            ('company_id', '=', self.env.company.id),
        ], limit=1) or self.env['account.analytic.account'].search([
            ('name', '=', 'Attività generale'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Registra Offerta',
            'res_model': 'volontariato.prima.nota.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tipo': 'entrata',
                'default_importo': self.offerta_euro,
                'default_data': self.data,
                'default_partner_id': self.richiedente_id.id,
                'default_journal_id': journal.id if journal else False,
                'default_conto_natura_id':
                    conto_offerte.id if conto_offerte else False,
                'default_analitica_id': analitica.id if analitica else False,
                'default_descrizione': 'Offerta intervento %s' % (
                    self.codice or ''),
                'default_intervento_id': self.id,
            },
        }

    def action_view_movimenti(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Movimenti Contabili',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('volontariato_intervento_id', '=', self.id)],
        }
