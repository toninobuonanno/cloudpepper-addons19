# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import date

from odoo import api, fields, models


class VolontariatoRendicontoWizard(models.TransientModel):
    _name = 'volontariato.rendiconto.wizard'
    _description = 'Rendiconto per Cassa - Selezione Periodo'

    anno = fields.Integer(
        string='Anno', required=True,
        default=lambda self: fields.Date.context_today(self).year,
    )
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
        required=True, readonly=True,
    )

    def action_stampa(self):
        self.ensure_one()
        return self.env.ref(
            'gestione_ass_volontariato_contabilita.action_report_rendiconto'
        ).report_action(self, data={
            'anno': self.anno, 'company_id': self.company_id.id,
        })


class ReportRendicontoCassa(models.AbstractModel):
    _name = 'report.gestione_ass_volontariato_contabilita.rendiconto'
    _description = 'Rendiconto per Cassa Mod. D'

    def _dati_rendiconto(self, anno, company):
        Line = self.env['account.move.line']
        date_from = date(anno, 1, 1)
        date_to = date(anno, 12, 31)
        base_domain = [
            ('company_id', '=', company.id),
            ('parent_state', '=', 'posted'),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ]
        lines = Line.search(base_domain + [
            ('volontariato_tipo', 'in', ('entrata', 'uscita')),
        ])

        sezioni = self.env['volontariato.sezione.rendiconto'].search([])
        dati = {s: {'entrate': defaultdict(float), 'uscite': defaultdict(float)}
                for s in sezioni}
        senza_sezione = {'entrate': defaultdict(float),
                         'uscite': defaultdict(float)}

        for line in lines:
            bucket = (dati.get(line.volontariato_sezione_id)
                      if line.volontariato_sezione_id else senza_sezione)
            if bucket is None:
                bucket = senza_sezione
            key = 'entrate' if line.volontariato_tipo == 'entrata' else 'uscite'
            bucket[key][line.account_id] += line.volontariato_importo

        # Saldi di liquidità a inizio e fine anno
        conti_liq = self.env['account.account'].with_company(company).search([
            ('account_type', '=', 'asset_cash'),
            ('company_ids', 'in', company.ids),
        ])
        def saldo_al(d):
            res = Line._read_group(
                [('company_id', '=', company.id),
                 ('parent_state', '=', 'posted'),
                 ('account_id', 'in', conti_liq.ids),
                 ('date', '<=', d)],
                [], ['balance:sum'],
            )
            return res[0][0] or 0.0

        tot_entrate = sum(v for s in list(dati.values()) + [senza_sezione]
                          for v in s['entrate'].values())
        tot_uscite = sum(v for s in list(dati.values()) + [senza_sezione]
                         for v in s['uscite'].values())

        return {
            'sezioni': [
                {
                    'sezione': s,
                    'entrate': sorted(dati[s]['entrate'].items(),
                                      key=lambda x: x[0].code),
                    'uscite': sorted(dati[s]['uscite'].items(),
                                     key=lambda x: x[0].code),
                    'tot_entrate': sum(dati[s]['entrate'].values()),
                    'tot_uscite': sum(dati[s]['uscite'].values()),
                }
                for s in sezioni
                if dati[s]['entrate'] or dati[s]['uscite']
            ],
            'senza_sezione': {
                'entrate': sorted(senza_sezione['entrate'].items(),
                                  key=lambda x: x[0].code),
                'uscite': sorted(senza_sezione['uscite'].items(),
                                 key=lambda x: x[0].code),
                'tot_entrate': sum(senza_sezione['entrate'].values()),
                'tot_uscite': sum(senza_sezione['uscite'].values()),
            },
            'tot_entrate': tot_entrate,
            'tot_uscite': tot_uscite,
            'avanzo': tot_entrate - tot_uscite,
            'saldo_iniziale': saldo_al(date(anno - 1, 12, 31)),
            'saldo_finale': saldo_al(date_to),
            'conti_liq': [
                (c, sum(l.balance for l in Line.search([
                    ('company_id', '=', company.id),
                    ('parent_state', '=', 'posted'),
                    ('account_id', '=', c.id),
                    ('date', '<=', date_to)])))
                for c in conti_liq
            ],
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        anno = (data or {}).get('anno') or fields.Date.today().year
        company = self.env['res.company'].browse(
            (data or {}).get('company_id') or self.env.company.id)
        valori = self._dati_rendiconto(anno, company)
        return {
            'doc_ids': docids,
            'doc_model': 'volontariato.rendiconto.wizard',
            'anno': anno,
            'company': company,
            **valori,
        }
