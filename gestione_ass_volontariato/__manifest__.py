# -*- coding: utf-8 -*-
{
    'name': 'Gestione Associazione Volontariato',
    'version': '19.0.2.5.1',
    'category': 'Volontariato',
    'summary': 'Gestione interventi, automezzi, volontari e dispositivi per associazioni di volontariato',
    'description': """
Gestione Associazione di Volontariato
=======================================
Modulo per associazioni di volontariato che svolgono trasporti sanitari
e assistenza con ambulanza. Funzionalità principali:

- Registro Interventi (fogli di viaggio)
- Squadra, paziente e consensi per ogni intervento
- Estensione Automezzi (Fleet) con sigla e contratti/assicurazioni
- Estensione Volontari (Employees) con qualifiche e certificazioni
- Dispositivi e attrezzature (Maintenance)
- Contratti e assicurazioni generali dell'associazione
""",
    'author': 'Misericordia Airola-Moiano',
    'website': 'https://misericordia.cloudpepper.site',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'hr',
        'fleet',
        'maintenance',
        'calendar',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequenze.xml',
        'data/cron.xml',
        'data/ruoli.xml',
        'data/tipi_intervento.xml',
        'data/calendar_event_types.xml',
        'views/ruolo_views.xml',
        'views/qualifica_views.xml',
        'views/tipo_cert_volontario_views.xml',
        'views/tipo_cert_attrezzatura_views.xml',
        'views/tipo_contratto_views.xml',
        'views/tipo_intervento_views.xml',
        'views/certificazione_volontario_views.xml',
        'views/hr_employee_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/maintenance_equipment_views.xml',
        'views/contratto_views.xml',
        'views/esercitazione_views.xml',
        'views/turno_views.xml',
        'views/impegno_volontari_views.xml',
        'report/turno_report.xml',
        'report/turni_periodo_report.xml',
        'report/impegno_volontari_report.xml',
        'views/turno_report_wizard_views.xml',
        'views/codice_fiscale_wizard_views.xml',
        'views/intervento_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
