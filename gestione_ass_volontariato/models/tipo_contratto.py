# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VolontariatoTipoContratto(models.Model):
    _name = 'volontariato.tipo.contratto'
    _description = 'Tipo Contratto / Assicurazione'
    _order = 'name'

    name = fields.Char(
        string='Nome', required=True,
        help='Es. Assicurazione RC, Assicurazione Infortuni, Contratto Ossigeno...'
    )
    active = fields.Boolean(string='Attivo', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Questo tipo di contratto esiste già.'),
    ]

    @api.constrains('name')
    def _check_name_unique(self):
        for record in self:
            duplicate = self.search([
                ('name', '=', record.name),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicate:
                raise ValidationError('Questo tipo di contratto esiste già: "%s"' % record.name)
