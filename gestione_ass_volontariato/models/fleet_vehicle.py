# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    volontariato_sigla = fields.Char(
        string='Sigla',
        help='Sigla interna del mezzo (es. A3, A4, A5...)',
    )
    volontariato_tipo_mezzo = fields.Selection(
        [
            ('ambulanza', 'Ambulanza'),
            ('auto', 'Automobile'),
            ('furgone', 'Furgone'),
            ('altro', 'Altro'),
        ],
        string='Tipo Mezzo',
        default='ambulanza',
    )

    @api.constrains('volontariato_sigla')
    def _check_sigla_unique(self):
        for record in self:
            if not record.volontariato_sigla:
                continue
            duplicate = self.search([
                ('volontariato_sigla', '=', record.volontariato_sigla),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    'Esiste già un mezzo con sigla "%s".' % record.volontariato_sigla
                )
