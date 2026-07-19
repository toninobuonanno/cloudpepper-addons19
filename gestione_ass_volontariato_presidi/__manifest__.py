# -*- coding: utf-8 -*-
{
    'name': 'Volontariato - Prestito Presidi',
    'version': '19.0.1.0.0',
    'category': 'Volontariato',
    'summary': 'Gestione a magazzino dei presidi sanitari donati: carico da '
               'donazioni e prestito/rientro ai richiedenti',
    'description': """
Prestito Presidi Sanitari
==========================
Gestisce i presidi sanitari donati all'associazione (letti ortopedici,
materassi antidecubito, aspiratori di secreti, pannoloni, ecc.) che
vengono prestati ai richiedenti e restituiti quando non più necessari.

Funzionalità principali:

- Anagrafica presidi con quantità a magazzino calcolata in tempo reale
  (donato - in prestito)
- Carico a magazzino da donazioni (donatore, data, righe per presidio)
- Prestiti ai richiedenti con tracciamento di fornitura e rientro,
  anche parziale
- Viste con filtri: presidi disponibili a magazzino, presidi forniti
  e non ancora rientrati
""",
    'author': 'Misericordia Airola-Moiano',
    'website': 'https://misericordia.cloudpepper.site',
    'license': 'LGPL-3',
    'depends': ['gestione_ass_volontariato'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequenze.xml',
        'views/presidio_views.xml',
        'views/presidio_donazione_views.xml',
        'views/presidio_prestito_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
