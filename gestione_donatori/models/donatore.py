# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DonatoriDonatore(models.Model):
    _name = 'donatori.donatore'
    _description = 'Donatore'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_names_search = ['name', 'tessera_nazionale', 'codice_fiscale']

    active = fields.Boolean(string='Attivo', default=True)

    # Dati SIF Fratres / anagrafica
    tessera_nazionale = fields.Char(
        string='Tessera Nazionale', required=True, index=True,
        help="Chiave usata dall'importazione per riconoscere il donatore "
             "nel file esportato da SIF Fratres.",
    )
    name = fields.Char(string='Soggetto', required=True, help='Cognome e Nome')
    sesso = fields.Selection(
        [('M', 'Maschio'), ('F', 'Femmina')], string='Sesso',
    )
    data_nascita = fields.Date(string='Data Nascita')
    eta = fields.Integer(string='Età', compute='_compute_eta')
    codice_fiscale = fields.Char(string='Codice Fiscale')
    comune_nascita = fields.Char(string='Comune di Nascita')

    tipologia = fields.Char(string='Tipologia', help='Es. Socio Donatore')
    gruppo_locale = fields.Char(string='Gruppo Locale')
    tessera_gruppo_locale = fields.Char(string='Tessera Gruppo Locale')
    data_iscrizione = fields.Date(string='Data Iscrizione')
    data_prenotazione = fields.Date(string='Data Prenotazione')
    sezione = fields.Char(string='Sezione')

    # Donazioni
    tipo_ultima_donazione = fields.Char(string='Tipo Ultima Donazione')
    data_ultima_donazione = fields.Date(string='Data Ultima Donazione')
    giorni_da_ultima_donazione = fields.Integer(
        string='Giorni da Ultima Donazione', compute='_compute_giorni_da_ultima_donazione',
    )
    numero_donazioni = fields.Integer(string='Numero Donazioni')

    # Dati sanitari
    gruppo_sanguigno = fields.Char(string='Gruppo Sanguigno')
    rh = fields.Char(string='Rh')
    fenotipo = fields.Char(string='Fenotipo')
    kell = fields.Char(string='Kell')

    # Contatti
    recapiti_telefonici = fields.Char(string='Recapiti Telefonici')
    telefono_fisso = fields.Char(string='Telefono Fisso')
    cellulare = fields.Char(string='Cellulare')
    recapiti_mail = fields.Char(string='Recapiti Mail')
    ultima_mail = fields.Date(string='Ultima Mail')
    ultimo_sms = fields.Date(string='Ultimo SMS')
    ultima_telefonata = fields.Date(string='Ultima Telefonata')

    # Residenza
    indirizzo_residenza = fields.Char(string='Indirizzo Residenza')
    localita_residenza = fields.Char(string='Località Residenza')
    cap_residenza = fields.Char(string='CAP Residenza')
    comune_residenza = fields.Char(string='Comune Residenza')

    # Domicilio
    indirizzo_domicilio = fields.Char(string='Indirizzo Domicilio')
    localita_domicilio = fields.Char(string='Località Domicilio')
    comune_domicilio = fields.Char(string='Comune Domicilio')
    cap_domicilio = fields.Char(string='CAP Domicilio')

    nazionalita = fields.Char(string='Nazionalità')
    cittadinanza = fields.Char(string='Cittadinanza')
    privacy_firmata = fields.Selection(
        [('si', 'Sì'), ('no', 'No')], string='Privacy Firmata',
    )
    riconoscimenti_assegnati = fields.Char(string='Riconoscimenti Assegnati')
    note = fields.Text(string='Note')

    data_ultimo_import = fields.Datetime(string='Ultimo Import', readonly=True)

    parametro_ids = fields.One2many(
        'donatori.parametro', 'donatore_id', string='Parametri Rilevati',
    )
    parametro_count = fields.Integer(compute='_compute_parametro_count')

    _sql_constraints = [
        ('tessera_nazionale_uniq', 'unique(tessera_nazionale)',
         'Esiste già un donatore con questa Tessera Nazionale.'),
    ]

    @api.depends('data_nascita')
    def _compute_eta(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.data_nascita:
                record.eta = (
                    today.year - record.data_nascita.year
                    - ((today.month, today.day) < (record.data_nascita.month, record.data_nascita.day))
                )
            else:
                record.eta = 0

    @api.depends('data_ultima_donazione')
    def _compute_giorni_da_ultima_donazione(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.data_ultima_donazione:
                record.giorni_da_ultima_donazione = (today - record.data_ultima_donazione).days
            else:
                record.giorni_da_ultima_donazione = 0

    def _compute_parametro_count(self):
        data = self.env['donatori.parametro']._read_group(
            [('donatore_id', 'in', self.ids)], ['donatore_id'], ['__count'],
        )
        counts = {donatore.id: count for donatore, count in data}
        for record in self:
            record.parametro_count = counts.get(record.id, 0)

    def action_view_parametri(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Parametri Rilevati',
            'res_model': 'donatori.parametro',
            'view_mode': 'list,form',
            'domain': [('donatore_id', '=', self.id)],
            'context': {'default_donatore_id': self.id},
        }
