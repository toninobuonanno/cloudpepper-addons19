# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VolontariatoRuolo(models.Model):
    _name = 'volontariato.ruolo'
    _description = 'Ruolo Squadra/Turno'
    _order = 'sequence, name'

    name = fields.Char(string='Nome Ruolo', required=True, help='Es. Caposquadra, Autista, Volontario...')
    sequence = fields.Integer(string='Sequenza', default=10)
    active = fields.Boolean(string='Attivo', default=True)
    is_responsabile = fields.Boolean(
        string='È Responsabile Unico',
        help='Se attivo, questo ruolo può essere assegnato a una sola persona per intervento/turno (es. Caposquadra).',
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Questo ruolo esiste già.'),
    ]

    @api.constrains('name')
    def _check_name_unique(self):
        for record in self:
            duplicate = self.search([
                ('name', '=', record.name),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicate:
                raise ValidationError('Questo ruolo esiste già: "%s"' % record.name)
