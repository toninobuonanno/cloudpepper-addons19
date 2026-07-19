# -*- coding: utf-8 -*-
import base64
import io
from collections import defaultdict

from odoo import api, fields, models, _


class VolontariatoReportEntrateUscite(models.TransientModel):
    _name = 'volontariato.report.entrate.uscite'
    _description = 'Report Periodico Entrate/Uscite'

    data_da = fields.Date(
        string='Data Da', required=True,
        default=lambda self: fields.Date.context_today(self).replace(
            month=1, day=1),
    )
    data_a = fields.Date(
        string='Data A', required=True,
        default=fields.Date.context_today,
    )
    journal_ids = fields.Many2many(
        'account.journal', string='Conti (Cassa/Banca)',
        domain="[('type', 'in', ('cash', 'bank')), ('company_id', '=', company_id)]",
        help='Vuoto = tutti',
    )
    analitica_ids = fields.Many2many(
        'account.analytic.account', string='Destinazioni',
        domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]",
        help='Vuoto = tutte',
    )
    conto_ids = fields.Many2many(
        'account.account', string='Nature (conti)',
        domain="[('account_type', 'in', ('income', 'income_other', 'expense', "
               "'expense_direct_cost')), ('company_ids', 'in', company_id)]",
        help='Vuoto = tutte',
    )
    partner_ids = fields.Many2many(
        'res.partner', string='Beneficiari', help='Vuoto = tutti',
    )
    includi_aperture = fields.Boolean(
        string='Includi Saldi di Apertura', default=False,
        help="Aggiunge al report le riprese saldo (aperture patrimoniali) "
             "come se fossero movimenti, replicando i totali del report "
             "di Money Manager Ex. Contabilmente le aperture non sono "
             "entrate/uscite dell'esercizio: usare solo per il confronto "
             "con i report MMEX. (Solo PDF ed Excel, non nella vista a "
             "video.)",
    )
    raggruppamento = fields.Selection(
        [
            ('elenco', 'Elenco movimenti'),
            ('natura', 'Per natura (conto)'),
            ('dest_natura', 'Per destinazione e natura (subtotali)'),
            ('partner_natura', 'Per beneficiario e natura'),
        ],
        string='Vista', required=True, default='dest_natura',
    )
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True,
    )

    # ─────────────────────────────────────────────────────────────
    def _get_domain(self):
        self.ensure_one()
        domain = [
            ('company_id', '=', self.company_id.id),
            ('parent_state', '=', 'posted'),
            ('volontariato_tipo', 'in', ('entrata', 'uscita')),
            ('date', '>=', self.data_da),
            ('date', '<=', self.data_a),
        ]
        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))
        if self.analitica_ids:
            domain.append(
                ('volontariato_analitica_id', 'in', self.analitica_ids.ids))
        if self.conto_ids:
            domain.append(('account_id', 'in', self.conto_ids.ids))
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        return domain

    def _get_dati(self):
        """Struttura: lista di gruppi di 1° livello, ognuno con
        sottogruppi di 2° livello e righe movimento."""
        self.ensure_one()
        lines = self.env['account.move.line'].search(
            self._get_domain(), order='date, id')

        def chiave_1(line):
            if self.raggruppamento == 'dest_natura':
                return (line.volontariato_analitica_id.name
                        or _('(senza destinazione)'))
            if self.raggruppamento == 'partner_natura':
                return line.partner_id.name or _('(senza beneficiario)')
            if self.raggruppamento == 'natura':
                return f'{line.account_id.code} {line.account_id.name}'
            return _('Tutti i movimenti')

        def chiave_2(line):
            if self.raggruppamento in ('dest_natura', 'partner_natura'):
                return f'{line.account_id.code} {line.account_id.name}'
            return None

        gruppi = defaultdict(lambda: {
            'sub': defaultdict(lambda: {'lines': [], 'e': 0.0, 'u': 0.0}),
            'e': 0.0, 'u': 0.0,
        })
        tot_e = tot_u = 0.0
        for line in lines:
            g1 = gruppi[chiave_1(line)]
            g2 = g1['sub'][chiave_2(line)]
            entrata = (line.volontariato_importo
                       if line.volontariato_tipo == 'entrata' else 0.0)
            uscita = (line.volontariato_importo
                      if line.volontariato_tipo == 'uscita' else 0.0)
            g2['lines'].append({
                'date': line.date, 'name': line.name or '',
                'partner': line.partner_id.name or '',
                'e': entrata, 'u': uscita,
            })
            g2['e'] += entrata
            g2['u'] += uscita
            g1['e'] += entrata
            g1['u'] += uscita
            tot_e += entrata
            tot_u += uscita

        gruppi_out = []

        # ── Saldi di apertura (opzionale, per confronto con MMEX) ──
        if self.includi_aperture:
            aperture = self.env['account.move.line'].search([
                ('company_id', '=', self.company_id.id),
                ('parent_state', '=', 'posted'),
                ('account_id.account_type', '=', 'equity'),
                ('name', '=', 'Saldo di apertura'),
                ('date', '>=', self.data_da),
                ('date', '<=', self.data_a),
            ], order='date, id')
            if aperture:
                rows, ape, apu = [], 0.0, 0.0
                for line in aperture:
                    e = line.credit if line.credit else 0.0
                    u = line.debit if line.debit else 0.0
                    conto_liq = line.move_id.line_ids.filtered(
                        lambda l: l.account_id.account_type == 'asset_cash'
                    )[:1].account_id
                    rows.append({
                        'date': line.date,
                        'name': 'Ripresa saldo %s' % (conto_liq.name or ''),
                        'partner': '',
                        'e': e, 'u': u,
                    })
                    ape += e
                    apu += u
                gruppi_out.append({
                    'nome': _('Saldi di apertura (ripresa saldo)'),
                    'e': ape, 'u': apu,
                    'sub': [{'nome': None, 'lines': rows,
                             'e': ape, 'u': apu}],
                })
                tot_e += ape
                tot_u += apu

        gruppi_out += [
                {
                    'nome': nome,
                    'e': g['e'], 'u': g['u'],
                    'sub': [
                        {'nome': sname, 'lines': s['lines'],
                         'e': s['e'], 'u': s['u']}
                        for sname, s in sorted(
                            g['sub'].items(), key=lambda x: x[0] or '')
                    ],
                }
                for nome, g in sorted(gruppi.items())
        ]
        # ── Saldi di liquidità ──
        Line = self.env['account.move.line']

        def saldo_liq(extra):
            res = Line._read_group([
                ('company_id', '=', self.company_id.id),
                ('parent_state', '=', 'posted'),
                ('account_id.account_type', '=', 'asset_cash'),
            ] + extra, [], ['balance:sum'])
            return res[0][0] or 0.0

        # Iniziale = saldo prima del periodo + eventuali aperture
        # (ripresa saldo) datate dentro il periodo
        saldo_iniziale = saldo_liq([('date', '<', self.data_da)]) + saldo_liq([
            ('date', '>=', self.data_da),
            ('date', '<=', self.data_a),
            ('name', '=', 'Saldo di apertura'),
        ])
        saldo_finale = saldo_liq([('date', '<=', self.data_a)])

        return {
            'gruppi': gruppi_out,
            'tot_e': tot_e,
            'tot_u': tot_u,
            'n_righe': len(lines),
            'saldo_iniziale': saldo_iniziale,
            'saldo_finale': saldo_finale,
        }

    # ── A VIDEO ──────────────────────────────────────────────────
    def action_visualizza(self):
        self.ensure_one()
        groupby = {
            'elenco': [],
            'natura': ['account_id'],
            'dest_natura': ['volontariato_analitica_id', 'account_id'],
            'partner_natura': ['partner_id', 'account_id'],
        }[self.raggruppamento]
        action = self.env['ir.actions.act_window']._for_xml_id(
            'gestione_ass_volontariato_contabilita.action_movimenti_prima_nota')
        action['domain'] = self._get_domain()
        action['context'] = {'group_by': groupby, 'expand': True}
        dati = self._get_dati()
        action['display_name'] = _(
            'Report %(da)s → %(a)s · Saldo iniziale %(si).2f € · '
            'Saldo finale %(sf).2f €',
            da=self.data_da.strftime('%d/%m/%Y'),
            a=self.data_a.strftime('%d/%m/%Y'),
            si=dati['saldo_iniziale'], sf=dati['saldo_finale'])
        return action

    # ── PDF ──────────────────────────────────────────────────────
    def action_pdf(self):
        self.ensure_one()
        return self.env.ref(
            'gestione_ass_volontariato_contabilita.action_report_entrate_uscite'
        ).report_action(self)

    # ── EXCEL ────────────────────────────────────────────────────
    def action_excel(self):
        self.ensure_one()
        import xlsxwriter
        dati = self._get_dati()
        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf, {'in_memory': True})
        ws = wb.add_worksheet('Entrate Uscite')

        f_title = wb.add_format({'bold': True, 'font_size': 14})
        f_head = wb.add_format({'bold': True, 'bg_color': '#4472C4',
                                'font_color': 'white', 'border': 1})
        f_g1 = wb.add_format({'bold': True, 'bg_color': '#D9E1F2'})
        f_g1n = wb.add_format({'bold': True, 'bg_color': '#D9E1F2',
                               'num_format': '#,##0.00'})
        f_g2 = wb.add_format({'bold': True, 'italic': True})
        f_g2n = wb.add_format({'bold': True, 'italic': True,
                               'num_format': '#,##0.00'})
        f_num = wb.add_format({'num_format': '#,##0.00'})
        f_date = wb.add_format({'num_format': 'dd/mm/yyyy'})
        f_tot = wb.add_format({'bold': True, 'top': 2,
                               'num_format': '#,##0.00'})

        ws.set_column(0, 0, 11)
        ws.set_column(1, 1, 45)
        ws.set_column(2, 2, 28)
        ws.set_column(3, 4, 14)

        ws.write(0, 0, '%s — Report Entrate/Uscite %s → %s' % (
            self.company_id.name,
            self.data_da.strftime('%d/%m/%Y'),
            self.data_a.strftime('%d/%m/%Y')), f_title)

        row = 2
        for col, head in enumerate(
                ['Data', 'Descrizione', 'Beneficiario', 'Entrate', 'Uscite']):
            ws.write(row, col, head, f_head)
        row += 1

        for g in dati['gruppi']:
            ws.write(row, 0, g['nome'], f_g1)
            ws.write(row, 1, '', f_g1)
            ws.write(row, 2, '', f_g1)
            ws.write_number(row, 3, g['e'], f_g1n)
            ws.write_number(row, 4, g['u'], f_g1n)
            row += 1
            for s in g['sub']:
                if s['nome']:
                    ws.write(row, 1, s['nome'], f_g2)
                    ws.write_number(row, 3, s['e'], f_g2n)
                    ws.write_number(row, 4, s['u'], f_g2n)
                    row += 1
                for line in s['lines']:
                    ws.write_datetime(row, 0,
                                      fields.Date.to_date(line['date']),
                                      f_date)
                    ws.write(row, 1, line['name'])
                    ws.write(row, 2, line['partner'])
                    if line['e']:
                        ws.write_number(row, 3, line['e'], f_num)
                    if line['u']:
                        ws.write_number(row, 4, line['u'], f_num)
                    row += 1

        ws.write(row, 1, 'TOTALE GENERALE', f_tot)
        ws.write(row, 2, '', f_tot)
        ws.write_number(row, 3, dati['tot_e'], f_tot)
        ws.write_number(row, 4, dati['tot_u'], f_tot)
        row += 1
        ws.write(row, 1, 'Differenza (avanzo/disavanzo)', f_tot)
        ws.write(row, 2, '', f_tot)
        ws.write_number(row, 3, dati['tot_e'] - dati['tot_u'], f_tot)
        ws.write(row, 4, '', f_tot)
        row += 2
        ws.write(row, 1, 'Saldo iniziale cassa e banca', f_g2)
        ws.write_number(row, 3, dati['saldo_iniziale'], f_g2n)
        row += 1
        ws.write(row, 1, 'Saldo finale cassa e banca', f_g2)
        ws.write_number(row, 3, dati['saldo_finale'], f_g2n)

        wb.close()
        filename = 'Report_Entrate_Uscite_%s_%s.xlsx' % (
            self.data_da.strftime('%Y%m%d'), self.data_a.strftime('%Y%m%d'))
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(buf.getvalue()),
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }


class ReportEntrateUscitePdf(models.AbstractModel):
    _name = 'report.gestione_ass_volontariato_contabilita.rep_eu'
    _description = 'Report Entrate/Uscite PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['volontariato.report.entrate.uscite'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'volontariato.report.entrate.uscite',
            'docs': wizard,
            'dati': {w.id: w._get_dati() for w in wizard},
        }
