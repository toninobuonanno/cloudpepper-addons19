# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def _column_exists(cr, table, column):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (table, column))
    return bool(cr.fetchone())


def migrate(cr, version):
    """Migra il campo tipo_intervento dei Turni:
    selection (char) -> tipo_intervento_id (Many2one volontariato.tipo.intervento).
    """
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})

    if _column_exists(cr, 'volontariato_turno', 'tipo_intervento'):
        mapping = {
            'emergenza': 'gestione_ass_volontariato.tipo_intervento_emergenza',
            'assistenza': 'gestione_ass_volontariato.tipo_intervento_assistenza',
            'trasporto': 'gestione_ass_volontariato.tipo_intervento_trasporto',
            'altro': 'gestione_ass_volontariato.tipo_intervento_altro',
        }
        for old_val, xmlid in mapping.items():
            tipo = env.ref(xmlid, raise_if_not_found=False)
            if tipo:
                cr.execute("""
                    UPDATE volontariato_turno
                    SET tipo_intervento_id = %s
                    WHERE tipo_intervento = %s
                      AND tipo_intervento_id IS NULL
                """, (tipo.id, old_val))
