# -*- coding: utf-8 -*-
import base64
import sqlite3
import tempfile
import os

from odoo import fields, models, _
from odoo.exceptions import UserError

# Mappatura sotto-categoria MMEX -> codice conto natura
# (chiavi minuscole; confronto case-insensitive)
MAPPA_NATURA = {
    'offerte': '3.01',
    'altre entrate': '3.99',
    'quote confederali': '4.01',
    'manutenzione': '4.02',
    'carburanti': '4.03',
    'ricariche ossigeno': '4.04',
    'ossigeno': '4.04',
    'amblanza': '4.05',          # refuso presente nei dati storici
    'ambulanza': '4.05',
    'volontari rc': '4.06',
    'volontari infortuni': '4.07',
    'csv quote': '4.08',
    'spese postali': '4.09',
    'cancelleria-tipografia': '4.10',
    'farmaci e presidi sanitari': '4.11',
    'apparecchiature medicali': '4.12',
    'manifestazioni': '4.13',
    'telefonino': '4.14',
    'internet': '4.14',
}

# Mappatura categoria (padre) MMEX -> (nome destinazione, lettera sezione)
MAPPA_DESTINAZIONE = {
    'ambulanza': ('Ambulanza', 'A'),
    'assicurazioni': ('Assicurazioni', 'A'),
    'entrate': ('Attività generale', 'A'),
    'income': ('Attività generale', 'A'),
    'confederazione': ('Confederazione', 'E'),
    'altre spese': ('Struttura', 'E'),
    'servizi': ('Struttura', 'E'),
    'tasse': ('Struttura', 'E'),
}

RIPRESA_SALDO = 'ripresa saldo'


class VolontariatoMmexImportWizard(models.TransientModel):
    _name = 'volontariato.mmex.import.wizard'
    _description = 'Importazione da Money Manager Ex'

    file_mmb = fields.Binary(string='File .mmb', required=True)
    file_name = fields.Char(string='Nome File')
    company_id = fields.Many2one(
        'res.company', string='Associazione (Company)',
        default=lambda self: self.env.company, required=True, readonly=True,
        help='I dati verranno importati nella company attiva. Per importare '
             'un\'altra associazione, cambiare company dal selettore in alto.',
    )
    esito = fields.Text(string='Esito', readonly=True)

    # ─────────────────────────────────────────────────────────────
    def _apri_db(self):
        raw = base64.b64decode(self.file_mmb)
        if not raw.startswith(b'SQLite format 3'):
            raise UserError(_(
                'Il file non sembra un database Money Manager Ex valido '
                '(.mmb). Verificare di aver caricato il file corretto.'))
        tmp = tempfile.NamedTemporaryFile(suffix='.mmb', delete=False)
        tmp.write(raw)
        tmp.close()
        return sqlite3.connect(tmp.name), tmp.name

    def _next_code(self, prefix, esistenti):
        """Primo codice libero nella fascia .50-.98 per conti auto-creati."""
        for i in range(50, 99):
            code = f'{prefix}.{i}'
            if code not in esistenti:
                return code
        raise UserError(_('Esauriti i codici disponibili nel mastro %s') % prefix)

    def _get_or_create_natura(self, sub_name, parent_name, is_income, cache):
        company = self.company_id
        key = (sub_name or parent_name or '').strip().lower()
        code = MAPPA_NATURA.get(key)
        if not code:
            code = '3.99' if is_income else '4.99'
            # Se la sotto-categoria ha un nome proprio non mappato,
            # creiamo un conto dedicato invece di buttare tutto in "Altre"
            if key and key not in ('altre spese', 'entrate', RIPRESA_SALDO):
                cached = cache.get('auto_' + key)
                if cached:
                    return cached
                esistenti = set(cache['tutti_codici'])
                new_code = self._next_code('3' if is_income else '4', esistenti)
                account = self.env['account.account'].with_company(company).create({
                    'code': new_code,
                    'name': (sub_name or parent_name).strip().capitalize(),
                    'account_type': 'income' if is_income else 'expense',
                    'company_ids': [(4, company.id)],
                })
                cache['tutti_codici'].append(new_code)
                cache['auto_' + key] = account
                return account
        account = cache.get(code)
        if not account:
            account = company._volontariato_get_account(code)
            cache[code] = account
        if not account:
            raise UserError(_('Conto %s non trovato: eseguire prima '
                              '"Configura contabilità ETS".') % code)
        return account

    def _get_or_create_destinazione(self, parent_name, plan, cache):
        company = self.company_id
        key = (parent_name or '').strip().lower()
        nome, lettera = MAPPA_DESTINAZIONE.get(
            key, ((parent_name or 'Attività generale').strip().capitalize(), False)
        )
        if nome in cache:
            return cache[nome]
        Analytic = self.env['account.analytic.account'].sudo()
        analytic = Analytic.search([
            ('name', '=', nome),
            ('plan_id', '=', plan.id),
            ('company_id', '=', company.id),
        ], limit=1)
        if not analytic:
            sezione = self.env['volontariato.sezione.rendiconto'].search(
                [('code', '=', lettera)], limit=1) if lettera else False
            analytic = Analytic.create({
                'name': nome,
                'plan_id': plan.id,
                'company_id': company.id,
                'sezione_rendiconto_id': sezione.id if sezione else False,
            })
        cache[nome] = analytic
        return analytic

    def _get_or_create_partner(self, payee_name, cache):
        key = (payee_name or '').strip().lower()
        if not key or key.startswith(RIPRESA_SALDO):
            return self.env['res.partner']
        if key in cache:
            return cache[key]
        Partner = self.env['res.partner']
        partner = Partner.search([
            ('name', '=ilike', payee_name.strip()),
            '|', ('company_id', '=', self.company_id.id),
            ('company_id', '=', False),
        ], limit=1)
        if not partner:
            partner = Partner.create({
                'name': payee_name.strip(),
                'company_id': self.company_id.id,
                'is_company': True,
            })
        cache[key] = partner
        return partner

    # ─────────────────────────────────────────────────────────────
    def action_importa(self):
        self.ensure_one()
        company = self.company_id
        plan = company._volontariato_setup_contabilita()

        con, tmp_path = self._apri_db()
        try:
            cur = con.cursor()

            # Categorie con gerarchia
            cats = {r[0]: (r[1], r[2]) for r in cur.execute(
                'SELECT CATEGID, CATEGNAME, PARENTID FROM CATEGORY_V1')}

            def split_cat(categ_id):
                """-> (nome_padre, nome_sotto) della categoria MMEX."""
                if categ_id not in cats:
                    return ('', '')
                name, parent = cats[categ_id]
                if parent in (None, -1) or parent not in cats:
                    return (name, '')
                return (cats[parent][0], name)

            # Conti MMEX -> giornali Odoo
            Journal = self.env['account.journal'].with_company(company)
            pnc = Journal.search([('code', '=', 'PNC'),
                                  ('company_id', '=', company.id)], limit=1)
            pnb = Journal.search([('code', '=', 'PNB'),
                                  ('company_id', '=', company.id)], limit=1)
            pnv = Journal.search([('code', '=', 'PNV'),
                                  ('company_id', '=', company.id)], limit=1)
            mmex_accounts = {}
            for aid, aname, atype in cur.execute(
                    'SELECT ACCOUNTID, ACCOUNTNAME, ACCOUNTTYPE '
                    'FROM ACCOUNTLIST_V1'):
                mmex_accounts[aid] = pnc if atype == 'Cash' else pnb

            patrimonio = company._volontariato_get_account('2.01')

            # Colonne (DELETEDTIME esiste dalle versioni recenti)
            cols = [r[1] for r in cur.execute(
                'PRAGMA table_info(CHECKINGACCOUNT_V1)')]
            has_deleted = 'DELETEDTIME' in cols

            query = ('SELECT TRANSID, ACCOUNTID, TOACCOUNTID, PAYEEID, '
                     'TRANSCODE, TRANSAMOUNT, TRANSACTIONNUMBER, NOTES, '
                     'CATEGID, TRANSDATE FROM CHECKINGACCOUNT_V1')
            if has_deleted:
                query += " WHERE (DELETEDTIME IS NULL OR DELETEDTIME='')"
            query += ' ORDER BY TRANSDATE, TRANSID'

            payees = {r[0]: r[1] for r in cur.execute(
                'SELECT PAYEEID, PAYEENAME FROM PAYEE_V1')}

            Move = self.env['account.move'].with_company(company)
            cache_conti = {'tutti_codici': [
                a.code for a in self.env['account.account'].with_company(
                    company).search([('company_ids', 'in', company.ids)])]}
            cache_dest = {}
            cache_partner = {}

            importati = saltati = aperture = 0
            errori = []

            for row in cur.execute(query).fetchall():
                (transid, accid, toaccid, payeeid, code, amount,
                 numero, note, categid, transdate) = row
                ref = f'MMEX:{transid}'
                if Move.search_count([('ref', '=', ref),
                                      ('company_id', '=', company.id)]):
                    saltati += 1
                    continue
                data = (transdate or '')[:10]
                if not data or not amount:
                    continue
                parent_name, sub_name = split_cat(categid)
                journal = mmex_accounts.get(accid, pnb)
                liquidita = journal.default_account_id
                descr = (note or '').strip() or (
                    f'{parent_name}: {sub_name}' if sub_name else parent_name
                ) or 'Movimento importato'
                partner = self._get_or_create_partner(
                    payees.get(payeeid, ''), cache_partner)

                try:
                    if (parent_name or '').strip().lower() == RIPRESA_SALDO:
                        # Saldo di apertura: liquidità a patrimonio
                        lines = [
                            (0, 0, {'account_id': liquidita.id,
                                    'debit': amount, 'credit': 0,
                                    'name': 'Saldo di apertura'}),
                            (0, 0, {'account_id': patrimonio.id,
                                    'debit': 0, 'credit': amount,
                                    'name': 'Saldo di apertura'}),
                        ]
                        move = Move.create({
                            'move_type': 'entry', 'journal_id': pnv.id,
                            'date': data, 'ref': ref,
                            'line_ids': lines,
                        })
                        move.action_post()
                        aperture += 1
                        continue

                    if code == 'Transfer':
                        dest_journal = mmex_accounts.get(toaccid, pnc)
                        lines = [
                            (0, 0, {'account_id':
                                    dest_journal.default_account_id.id,
                                    'debit': amount, 'credit': 0,
                                    'name': descr}),
                            (0, 0, {'account_id': liquidita.id,
                                    'debit': 0, 'credit': amount,
                                    'name': descr}),
                        ]
                        move = Move.create({
                            'move_type': 'entry', 'journal_id': pnv.id,
                            'date': data, 'ref': ref, 'line_ids': lines,
                        })
                        move.action_post()
                        importati += 1
                        continue

                    is_income = code == 'Deposit'
                    natura = self._get_or_create_natura(
                        sub_name, parent_name, is_income, cache_conti)
                    dest = self._get_or_create_destinazione(
                        parent_name, plan, cache_dest)

                    line_nat = {
                        'account_id': natura.id,
                        'name': descr,
                        'partner_id': partner.id or False,
                        'analytic_distribution': {str(dest.id): 100},
                        'volontariato_analitica_id': dest.id,
                        'debit': 0 if is_income else amount,
                        'credit': amount if is_income else 0,
                    }
                    line_liq = {
                        'account_id': liquidita.id,
                        'name': descr,
                        'partner_id': partner.id or False,
                        'debit': amount if is_income else 0,
                        'credit': 0 if is_income else amount,
                    }
                    move = Move.create({
                        'move_type': 'entry',
                        'journal_id': journal.id,
                        'date': data,
                        'ref': ref,
                        'partner_id': partner.id or False,
                        'line_ids': [(0, 0, line_liq), (0, 0, line_nat)],
                    })
                    move.action_post()
                    importati += 1
                except Exception as e:
                    errori.append(f'{data} {descr}: {e}')

            esito = _(
                'Importazione completata per %(company)s.\n'
                '- Movimenti importati: %(n)d\n'
                '- Saldi di apertura: %(a)d\n'
                '- Già presenti (saltati): %(s)d',
                company=company.name, n=importati, a=aperture, s=saltati)
            if errori:
                esito += _('\n\nErrori (%d):\n') % len(errori)
                esito += '\n'.join(errori[:15])
            self.esito = esito
        finally:
            con.close()
            os.unlink(tmp_path)

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
