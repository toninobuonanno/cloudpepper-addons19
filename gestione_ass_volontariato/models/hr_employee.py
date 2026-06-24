# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    volontariato_qualifica_id = fields.Many2one(
        'volontariato.qualifica',
        string='Qualifica Volontario',
        help='Qualifica operativa del volontario (es. Soccorritore, Autista Soccorritore...)',
    )
    volontariato_nr_primis = fields.Char(
        string='Nr. Primis',
        help='Numero identificativo Primis del volontario',
    )
    volontariato_cert_ids = fields.One2many(
        'volontariato.certificazione.volontario',
        'employee_id',
        string='Certificazioni',
    )
    volontariato_cert_count = fields.Integer(
        string='Numero Certificazioni',
        compute='_compute_volontariato_cert_count',
    )

    def _compute_volontariato_cert_count(self):
        for employee in self:
            employee.volontariato_cert_count = len(employee.volontariato_cert_ids)
