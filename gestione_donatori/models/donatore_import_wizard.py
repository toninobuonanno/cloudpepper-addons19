# -*- coding: utf-8 -*-
import base64
import io
from datetime import date, datetime

from odoo import _, fields, models
from odoo.exceptions import UserError

try:
    import openpyxl
except ImportError:
    openpyxl = None


# Corrispondenza tra le intestazioni del file esportato da SIF Fratres
# e i campi di donatori.donatore. 'Età' e 'Giorni da Ultima Donazione'
# non compaiono perché sono calcolati automaticamente dal modulo.
FIELD_MAP = {
    'Tessera Nazionale': 'tessera_nazionale',
    'Soggetto': 'name',
    'Sesso': 'sesso',
    'Data Nascita': 'data_nascita',
    'Codice Fiscale': 'codice_fiscale',
    'Tipologia': 'tipologia',
    'Gruppo Locale': 'gruppo_locale',
    'Tessera Gruppo Locale': 'tessera_gruppo_locale',
    'Data iscrizione': 'data_iscrizione',
    'Data prenotazione': 'data_prenotazione',
    'Sezione': 'sezione',
    'Tipo Ultima Donazione': 'tipo_ultima_donazione',
    'Data Ultima Donazione': 'data_ultima_donazione',
    'Numero Donazioni': 'numero_donazioni',
    'Gruppo sanguigno': 'gruppo_sanguigno',
    'Rh': 'rh',
    'Fenotipo': 'fenotipo',
    'Kell': 'kell',
    'Recapiti telefonici': 'recapiti_telefonici',
    'Telefono Fisso': 'telefono_fisso',
    'Cellulare': 'cellulare',
    'Recapiti mail': 'recapiti_mail',
    'Note': 'note',
    'Ultima mail': 'ultima_mail',
    'Ultimo sms': 'ultimo_sms',
    'Ultima telefonata': 'ultima_telefonata',
    'Indirizzo Residenza': 'indirizzo_residenza',
    'Località Residenza': 'localita_residenza',
    'CAP Residenza': 'cap_residenza',
    'Comune Residenza': 'comune_residenza',
    'Indirizzo Domicilio': 'indirizzo_domicilio',
    'Località Domicilio': 'localita_domicilio',
    'Comune Domicilio': 'comune_domicilio',
    'CAP Domicilio': 'cap_domicilio',
    'Comune di Nascita': 'comune_nascita',
    'Nazionalità': 'nazionalita',
    'Cittadinanza': 'cittadinanza',
    'Privacy Firmata': 'privacy_firmata',
    'Riconoscimenti Assegnati': 'riconoscimenti_assegnati',
}

DATE_FIELDS = {
    'data_nascita', 'data_iscrizione', 'data_prenotazione',
    'data_ultima_donazione', 'ultima_mail', 'ultimo_sms', 'ultima_telefonata',
}
INT_FIELDS = {'numero_donazioni'}
SI_NO_FIELDS = {'privacy_firmata'}


class DonatoriDonatoreImportWizard(models.TransientModel):
    _name = 'donatori.donatore.import.wizard'
    _description = 'Importa Anagrafica Donatori da SIF Fratres'

    file = fields.Binary(string='File Excel', required=True)
    filename = fields.Char(string='Nome File')
    state = fields.Selection(
        [('input', 'Input'), ('done', 'Fatto')], default='input',
    )
    created_count = fields.Integer(string='Creati', readonly=True)
    updated_count = fields.Integer(string='Aggiornati', readonly=True)
    error_count = fields.Integer(string='Errori', readonly=True)
    log = fields.Text(string='Dettaglio', readonly=True)

    @staticmethod
    def _parse_date(value):
        if not value:
            return False
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        text = str(value).strip()
        if not text:
            return False
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return False

    @staticmethod
    def _parse_str(value):
        if value is None:
            return False
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        text = str(value).strip()
        return text or False

    @staticmethod
    def _parse_int(value):
        if value in (None, ''):
            return 0
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_si_no(value):
        text = str(value).strip().lower() if value is not None else ''
        if text in ('si', 'sì', 'yes', '1', 'true'):
            return 'si'
        if text in ('no', '0', 'false'):
            return 'no'
        return False

    def action_import(self):
        self.ensure_one()
        if openpyxl is None:
            raise UserError(_(
                "La libreria Python 'openpyxl' non è disponibile sul "
                "server: contattare l'amministratore per installarla."
            ))
        if not self.file:
            raise UserError(_("Seleziona un file Excel da importare."))

        try:
            workbook = openpyxl.load_workbook(
                io.BytesIO(base64.b64decode(self.file)),
                data_only=True, read_only=True,
            )
        except Exception as e:
            raise UserError(_("Impossibile leggere il file Excel: %s") % e)

        sheet = workbook.worksheets[0]
        rows = sheet.iter_rows(values_only=True)
        try:
            header = next(rows)
        except StopIteration:
            raise UserError(_("Il file selezionato è vuoto."))

        header_index = {}
        for idx, label in enumerate(header):
            if isinstance(label, str):
                label = label.strip()
            if label in FIELD_MAP:
                header_index[FIELD_MAP[label]] = idx

        if 'tessera_nazionale' not in header_index:
            raise UserError(_(
                "Colonna 'Tessera Nazionale' non trovata nel file. "
                "Verificare di aver selezionato l'export corretto da "
                "SIF Fratres."
            ))

        Donatore = self.env['donatori.donatore']
        created = updated = errors = 0
        error_lines = []
        now = fields.Datetime.now()

        for row_num, row in enumerate(rows, start=2):
            tessera = self._parse_str(row[header_index['tessera_nazionale']])
            if not tessera:
                continue
            try:
                values = {'data_ultimo_import': now}
                for field_name, col_idx in header_index.items():
                    if col_idx >= len(row):
                        continue
                    raw = row[col_idx]
                    if field_name in DATE_FIELDS:
                        values[field_name] = self._parse_date(raw)
                    elif field_name in INT_FIELDS:
                        values[field_name] = self._parse_int(raw)
                    elif field_name in SI_NO_FIELDS:
                        values[field_name] = self._parse_si_no(raw)
                    else:
                        values[field_name] = self._parse_str(raw)

                donatore = Donatore.search(
                    [('tessera_nazionale', '=', tessera)], limit=1,
                )
                if donatore:
                    donatore.write(values)
                    updated += 1
                else:
                    values.setdefault('name', tessera)
                    Donatore.create(values)
                    created += 1
            except Exception as e:
                errors += 1
                error_lines.append(
                    _("Riga %s (tessera %s): %s") % (row_num, tessera, e)
                )

        self.write({
            'state': 'done',
            'created_count': created,
            'updated_count': updated,
            'error_count': errors,
            'log': '\n'.join(error_lines) if error_lines else _('Nessun errore.'),
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'donatori.donatore.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
