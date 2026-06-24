# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VolontariatoQualifica(models.Model):
    _name = 'volontariato.qualifica'
    _description = 'Qualifica Volontario'
    _order = 'name'

    name = fields.Char(string='Nome Qualifica', required=True)
    active = fields.Boolean(string='Attivo', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Questa qualifica esiste già.'),
    ]

    @api.constrains('name')
    def _check_name_unique(self):
        for record in self:
            duplicate = self.search([
                ('name', '=', record.name),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicate:
                raise ValidationError('Questa qualifica esiste già: "%s"' % record.name)
