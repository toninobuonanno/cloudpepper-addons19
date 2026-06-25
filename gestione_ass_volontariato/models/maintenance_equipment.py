# -*- coding: utf-8 -*-
from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    volontariato_cert_ids = fields.One2many(
        'volontariato.certificazione.attrezzatura',
        'equipment_id',
        string='Certificazioni',
    )
    volontariato_cert_count = fields.Integer(
        string='Numero Certificazioni',
        compute='_compute_volontariato_cert_count',
    )

    def _compute_volontariato_cert_count(self):
        for equipment in self:
            equipment.volontariato_cert_count = len(equipment.volontariato_cert_ids)
