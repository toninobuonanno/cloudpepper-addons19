# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VolontariatoTipoEsercitazione(models.Model):
    _name = 'volontariato.tipo.esercitazione'
    _description = 'Tipologia Esercitazione'
    _order = 'name'

    name = fields.Char(
        string='Nome', required=True,
        help='Es. Soccorso stradale, Manovre BLS, Trasporto barella...'
    )
    active = fields.Boolean(string='Attivo', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Questa tipologia esiste già.'),
    ]

    @api.constrains('name')
    def _check_name_unique(self):
        for record in self:
            duplicate = self.search([
                ('name', '=', record.name),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicate:
                raise ValidationError('Questa tipologia esiste già: "%s"' % record.name)
