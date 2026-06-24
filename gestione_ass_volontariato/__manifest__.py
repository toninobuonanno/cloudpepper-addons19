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
        'views/qualifica_views.xml',
        'views/tipo_cert_volontario_views.xml',
        'views/tipo_cert_attrezzatura_views.xml',
        'views/tipo_contratto_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
