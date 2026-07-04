# -*- coding: utf-8 -*-
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

        gender_map = {'male': 'M', 'female': 'F'}
        res['sesso'] = gender_map.get(employee.gender, False)

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

        return res

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
        try:
            codice = cf_lib.encode(
                lastname=self.cognome,
                firstname=self.nome,
                gender=self.sesso,
                birthdate=self.data_nascita.strftime('%d/%m/%Y'),
                birthplace=self.luogo_nascita,
            )
        except Exception as e:
            raise UserError(_(
                "Impossibile calcolare il codice fiscale.\n\n"
                "Verificare che il Comune/Stato di nascita sia scritto "
                "correttamente e che la data sia coerente.\n\n"
                "Dettaglio tecnico: %s"
            ) % e)

        self.employee_id.write({
            'volontariato_codice_fiscale': codice,
            # Riporta anche i dati anagrafici sulla scheda se mancanti
            'birthday': self.employee_id.birthday or self.data_nascita,
            'place_of_birth': self.employee_id.place_of_birth
            or self.luogo_nascita,
        })
        return {'type': 'ir.actions.act_window_close'}
