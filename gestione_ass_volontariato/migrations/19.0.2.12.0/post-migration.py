# -*- coding: utf-8 -*-
from markupsafe import escape


def _column_exists(cr, table, column):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (table, column))
    return bool(cr.fetchone())


def migrate(cr, version):
    """Converte il campo 'note' (già passato da testo semplice a HTML) di
    Contratti/Assicurazioni e Registro Esercitazioni, mantenendo gli a capo
    esistenti come <br/> invece di perderli in un'unica riga.
    """
    if not version:
        return

    tables = ['volontariato_contratto', 'volontariato_esercitazione']
    for table in tables:
        if not _column_exists(cr, table, 'note'):
            continue
        cr.execute(f"SELECT id, note FROM {table} WHERE note IS NOT NULL AND note != ''")
        rows = cr.fetchall()
        for row_id, note in rows:
            html_note = str(escape(note)).replace('\n', '<br/>\n')
            cr.execute(f"UPDATE {table} SET note = %s WHERE id = %s", (html_note, row_id))
