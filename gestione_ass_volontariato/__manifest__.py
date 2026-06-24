# -*- coding: utf-8 -*-
{
    'name': 'Gestione Associazione Volontariato',
    'version': '19.0.1.0.0',
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
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
