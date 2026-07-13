# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    from codicefiscale import codicefiscale as cf_lib
except ImportError:
    cf_lib = None


class VolontariatoCodiceFiscaleWizard(models.TransientModel):
    _name = 'volontariato.codice.fiscale.wizard'
    _description = 'Calcolo Codice Fiscale'

    employee_id = fields.Many2one(
        'hr.employee', string='Volontario', required=True, readonly=True,
    )
    cognome = fields.Char(string='Cognome', required=True)
    nome = fields.Char(string='Nome', required=True)
    sesso = fields.Selection(
        [('M', 'Maschio'), ('F', 'Femmina')],
        string='Sesso', required=True,
    )
    data_nascita = fields.Date(string='Data di Nascita', required=True)
    luogo_nascita = fields.Char(
        string='Comune / Stato di Nascita', required=True,
        help="Comune italiano di nascita (es. Airola) oppure, per i nati "
             "all'estero, il nome dello Stato (es. Germania).",
    )
    provincia_nascita_id = fields.Many2one(
        'res.country.state', string='Provincia di Nascita',
        domain="[('country_id.code', '=', 'IT')]",
        help="Provincia del comune di nascita. Necessaria per calcolare "
             "correttamente il codice fiscale quando più comuni italiani "
             "hanno lo stesso nome in province diverse. Lasciare vuoto "
             "per i nati all'estero.",
    )
    codice_fiscale = fields.Char(
        string='Codice Fiscale Calcolato', readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        employee = self.env['hr.employee'].browse(
            self.env.context.get('active_id')
        )
        if not employee:
            return res

        res['employee_id'] = employee.id

        # Divisione nome/cognome: negli archivi il formato è "Cognome Nome",
        # quindi la prima parola è il cognome e il resto il nome.
        # L'utente può comunque correggere nel wizard.
        parts = (employee.name or '').strip().split()
        if len(parts) >= 2:
            res['cognome'] = parts[0]
            res['nome'] = ' '.join(parts[1:])
        elif parts:
            res['cognome'] = parts[0]

        if employee.birthday:
            res['data_nascita'] = employee.birthday

        # In Odoo 19 il campo si chiama 'sex' (su hr.version, delegato a
        # hr.employee); nelle versioni precedenti era 'gender'.
        gender_map = {'male': 'M', 'female': 'F'}
        sex_value = False
        for field_name in ('sex', 'gender'):
            if field_name in employee._fields:
                sex_value = employee[field_name]
                break
        res['sesso'] = gender_map.get(sex_value, False)

        # Luogo: se nato all'estero usa lo Stato, altrimenti il comune
        italy = self.env.ref('base.it', raise_if_not_found=False)
        if (
            employee.country_of_birth
            and italy
            and employee.country_of_birth != italy
        ):
            res['luogo_nascita'] = employee.country_of_birth.name
        elif employee.place_of_birth:
            res['luogo_nascita'] = employee.place_of_birth
            if employee.volontariato_provincia_nascita_id:
                res['provincia_nascita_id'] = employee.volontariato_provincia_nascita_id.id

        return res

    @staticmethod
    def _birthplace_candidates(luogo, provincia_code):
        """Varianti del luogo di nascita da tentare in ordine.

        I registri anagrafici spesso abbreviano "Santo/Santa/Sant'" in
        "S.": la libreria di calcolo richiede invece il nome ufficiale
        ISTAT per esteso, quindi generiamo le espansioni più comuni.
        La provincia, quando indicata, viene accodata tra parentesi per
        distinguere i comuni omonimi in province diverse.
        """
        luogo = (luogo or '').strip()
        candidates = [luogo]
        match = re.match(r"^[Ss]\.?\s+(.+)$", luogo)
        if match:
            resto = match.group(1)
            candidates += [
                'San %s' % resto,
                'Santa %s' % resto,
                "Sant'%s" % resto,
            ]
        if provincia_code:
            candidates = ['%s (%s)' % (c, provincia_code) for c in candidates]
        return candidates

    def action_calcola(self):
        self.ensure_one()
        if cf_lib is None:
            raise UserError(_(
                "La libreria Python 'python-codicefiscale' non è installata "
                "sul server.\n\nInstallarla con:\n"
                "pip3 install python-codicefiscale\n\n"
                "oppure tramite il pannello di gestione dell'hosting "
                "(dipendenze Python / requirements.txt)."
            ))
        provincia_code = (
            self.provincia_nascita_id.code if self.provincia_nascita_id else None
        )
        candidates = self._birthplace_candidates(self.luogo_nascita, provincia_code)

        codice = None
        last_error = None
        for birthplace in candidates:
            try:
                codice = cf_lib.encode(
                    lastname=self.cognome,
                    firstname=self.nome,
                    gender=self.sesso,
                    birthdate=self.data_nascita.strftime('%d/%m/%Y'),
                    birthplace=birthplace,
                )
                break
            except Exception as e:
                last_error = e

        if codice is None:
            raise UserError(_(
                "Impossibile calcolare il codice fiscale.\n\n"
                "Verificare che il Comune/Stato di nascita sia scritto "
                "correttamente (nome ufficiale del comune) e che la data "
                "sia coerente. Se il comune esiste in più province, "
                "indicare anche la Provincia di nascita.\n\n"
                "Dettaglio tecnico: %s"
            ) % last_error)

        self.employee_id.write({
            'volontariato_codice_fiscale': codice,
            # Riporta anche i dati anagrafici sulla scheda se mancanti
            'birthday': self.employee_id.birthday or self.data_nascita,
            'place_of_birth': self.employee_id.place_of_birth
            or self.luogo_nascita,
            'volontariato_provincia_nascita_id': (
                self.employee_id.volontariato_provincia_nascita_id.id
                or self.provincia_nascita_id.id
            ),
        })
        return {'type': 'ir.actions.act_window_close'}
