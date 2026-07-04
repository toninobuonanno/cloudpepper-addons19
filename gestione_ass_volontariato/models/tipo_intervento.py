# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VolontariatoTipoIntervento(models.Model):
    _name = 'volontariato.tipo.intervento'
    _description = 'Tipologia Intervento'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nome', required=True,
        help='Es. Emergenza, Assistenza, Trasporto...'
    )
    sequence = fields.Integer(string='Sequenza', default=10)
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
