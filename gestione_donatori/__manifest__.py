# -*- coding: utf-8 -*-
{
    'name': 'Gestione Donatori',
    'version': '19.0.1.1.0',
    'category': 'Volontariato',
    'summary': 'Anagrafica donatori di sangue con import da SIF Fratres e '
               'registrazione parametri pre-donazione',
    'description': """
Gestione Donatori
==================
Modulo per la gestione dei donatori di sangue di un gruppo Fratres.
Funzionalità principali:

- Anagrafica Donatori, indipendente dai Dipendenti, con tutti i dati
  esportati dal sistema nazionale SIF Fratres
- Importazione periodica dell'anagrafica da file Excel esportato da SIF
  Fratres, con la Tessera Nazionale come chiave: crea i donatori nuovi
  e aggiorna quelli già presenti
- Registrazione dei Parametri Donatori rilevati nelle fasi preliminari
  alle donazioni (peso, pressione arteriosa, frequenza cardiaca,
  emoglobina, idoneità, note)
""",
    'author': 'Misericordia Airola-Moiano',
    'website': 'https://misericordia.cloudpepper.site',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'data': [
        'security/donatori_security.xml',
        'security/ir.model.access.csv',
        'views/donatore_views.xml',
        'views/parametro_views.xml',
        'views/donatore_import_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
