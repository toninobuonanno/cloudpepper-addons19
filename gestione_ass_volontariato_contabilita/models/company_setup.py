# -*- coding: utf-8 -*-
from odoo import api, models

# Piano dei conti minimale ETS: (codice, nome, account_type)
CONTI_ETS = [
    ('1.01', 'Cassa contanti', 'asset_cash'),
    ('1.02', 'Banca c/c', 'asset_cash'),
    ('2.01', 'Patrimonio netto', 'equity'),
    ('2.02', 'Risultato di gestione', 'equity_unaffected'),
    ('3.01', 'Offerte ed erogazioni liberali', 'income'),
    ('3.02', 'Cinque per mille', 'income'),
    ('3.03', 'Quote associative', 'income'),
    ('3.04', 'Raccolte fondi', 'income'),
    ('3.05', 'Contributi da enti pubblici', 'income'),
    ('3.99', 'Altre entrate', 'income'),
    ('4.01', 'Quote confederali', 'expense'),
    ('4.02', 'Manutenzione automezzi', 'expense'),
    ('4.03', 'Carburanti', 'expense'),
    ('4.04', 'Ricariche ossigeno', 'expense'),
    ('4.05', 'Assicurazione automezzi', 'expense'),
    ('4.06', 'Assicurazione volontari RC', 'expense'),
    ('4.07', 'Assicurazione volontari infortuni', 'expense'),
    ('4.08', 'Quote CSV', 'expense'),
    ('4.09', 'Spese postali', 'expense'),
    ('4.10', 'Cancelleria e tipografia', 'expense'),
    ('4.11', 'Farmaci e presidi sanitari', 'expense'),
    ('4.12', 'Apparecchiature medicali', 'expense'),
    ('4.13', 'Manifestazioni ed eventi', 'expense'),
    ('4.14', 'Utenze e telefonia', 'expense'),
    ('4.99', 'Altre uscite', 'expense'),
]

GIORNALI_ETS = [
    ('PNC', 'Prima Nota Cassa', 'cash', '1.01'),
    ('PNB', 'Prima Nota Banca', 'bank', '1.02'),
    ('PNV', 'Operazioni Varie', 'general', None),
]


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _volontariato_get_account(self, code):
        """Restituisce il conto con quel codice per questa company."""
        self.ensure_one()
        return self.env['account.account'].with_company(self).search([
            ('code', '=', code),
            ('company_ids', 'in', self.ids),
        ], limit=1)

    def _volontariato_setup_contabilita(self):
        """Crea (se mancanti) conti, giornali e piano analitico ETS
        per questa company. Rieseguibile senza effetti collaterali."""
        self.ensure_one()
        Account = self.env['account.account'].with_company(self)
        Journal = self.env['account.journal'].with_company(self)

        # ── Conti ──
        conti = {}
        for code, name, acc_type in CONTI_ETS:
            account = self._volontariato_get_account(code)
            if not account:
                account = Account.create({
                    'code': code,
                    'name': name,
                    'account_type': acc_type,
                    'company_ids': [(4, self.id)],
                })
            conti[code] = account

        # ── Giornali ──
        for jcode, jname, jtype, default_code in GIORNALI_ETS:
            journal = Journal.search([
                ('code', '=', jcode),
                ('company_id', '=', self.id),
            ], limit=1)
            if not journal:
                vals = {
                    'code': jcode,
                    'name': jname,
                    'type': jtype,
                    'company_id': self.id,
                }
                if default_code:
                    vals['default_account_id'] = conti[default_code].id
                Journal.create(vals)

        # ── Piano analitico + destinazione di default ──
        # In Odoo 19 il piano analitico è condiviso tra le company;
        # sono i singoli conti analitici ad avere la company.
        Plan = self.env['account.analytic.plan'].sudo()
        plan = Plan.search([('name', '=', 'Destinazioni')], limit=1)
        if not plan:
            plan = Plan.create({'name': 'Destinazioni'})

        Analytic = self.env['account.analytic.account'].sudo()
        default_analytic = Analytic.search([
            ('name', '=', 'Attività generale'),
            ('plan_id', '=', plan.id),
            ('company_id', '=', self.id),
        ], limit=1)
        if not default_analytic:
            sezione_a = self.env.ref(
                'gestione_ass_volontariato_contabilita.sezione_rendiconto_a',
                raise_if_not_found=False,
            )
            Analytic.create({
                'name': 'Attività generale',
                'plan_id': plan.id,
                'company_id': self.id,
                'sezione_rendiconto_id': sezione_a.id if sezione_a else False,
            })
        return plan

    def action_volontariato_setup_contabilita(self):
        for company in self:
            company._volontariato_setup_contabilita()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Contabilità ETS',
                'message': 'Piano dei conti, giornali e piano analitico '
                           'configurati per %s.' % ', '.join(self.mapped('name')),
                'type': 'success',
            },
        }
