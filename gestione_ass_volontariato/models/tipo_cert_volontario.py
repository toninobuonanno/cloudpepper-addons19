# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VolontariatoTipoCertVolontario(models.Model):
    _name = 'volontariato.tipo.cert.volontario'
    _description = 'Tipo Certificazione Volontario'
    _order = 'name'

    name = fields.Char(string='Nome', required=True, help='Es. BLS, BLS-D, PBLSD...')
    active = fields.Boolean(string='Attivo', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Questo tipo di certificazione esiste già.'),
    ]

    @api.constrains('name')
    def _check_name_unique(self):
        for record in self:
            duplicate = self.search([
                ('name', '=', record.name),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicate:
                raise ValidationError('Questo tipo di certificazione esiste già: "%s"' % record.name)
