# -*- coding: utf-8 -*-
{
    'name': 'Volontariato - Contabilità ETS',
    'version': '19.0.1.0.4',
    'category': 'Accounting',
    'summary': 'Prima nota semplificata, rendiconto per cassa Mod. D e '
               'importatore Money Manager Ex per associazioni di volontariato',
    'description': """
Contabilità per Enti del Terzo Settore
======================================
- Piano dei conti minimale ETS (mastri: 1 liquidità, 2 patrimonio,
  3 entrate, 4 uscite)
- Destinazioni (conti analitici) con sezione del Rendiconto per cassa
  Mod. D (D.M. 5/3/2020) configurabile
- Prima nota semplificata: entrate/uscite senza partita doppia manuale
- Rendiconto per cassa PDF per anno
- Importatore da Money Manager Ex (.mmb), multi-company e rieseguibile
- Registrazione offerte direttamente dal Registro Interventi
""",
    'author': 'Confraternita di Misericordia',
    'license': 'LGPL-3',
    'depends': [
        'gestione_ass_volontariato',
        'account',
        'analytic',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sezioni_rendiconto.xml',
        'views/sezione_views.xml',
        'views/analytic_views.xml',
        'views/prima_nota_wizard_views.xml',
        'views/movimenti_views.xml',
        'views/mmex_import_views.xml',
        'views/rendiconto_wizard_views.xml',
        'views/intervento_views.xml',
        'report/rendiconto_report.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
