# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    sezione_rendiconto_id = fields.Many2one(
        'volontariato.sezione.rendiconto',
        string='Sezione Rendiconto (Mod. D)',
        help='Sezione del rendiconto per cassa in cui confluiscono i '
             'movimenti di questa destinazione. Modificabile in qualsiasi '
             'momento: la riclassificazione ha effetto anche sui movimenti '
             'già registrati alla prossima generazione del rendiconto.',
    )
