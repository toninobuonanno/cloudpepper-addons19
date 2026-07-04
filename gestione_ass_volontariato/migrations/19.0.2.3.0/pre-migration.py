# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Preserva i vecchi valori prima dell'aggiornamento dello schema.

    - richiedente_citta / richiedente_provincia diventano campi related
      (verranno ricalcolati dal partner), quindi copiamo i valori attuali
      in colonne temporanee per usarli nella post-migrazione.
    - Le colonne 'tipo_intervento' (selection) e 'richiedente' (char)
      restano nel DB e verranno lette dalla post-migrazione.
    """
    if not version:
        return

    cr.execute("""
        ALTER TABLE volontariato_intervento
        ADD COLUMN IF NOT EXISTS richiedente_citta_legacy varchar
    """)
    cr.execute("""
        ALTER TABLE volontariato_intervento
        ADD COLUMN IF NOT EXISTS richiedente_provincia_legacy varchar
    """)
    cr.execute("""
        UPDATE volontariato_intervento
        SET richiedente_citta_legacy = richiedente_citta,
            richiedente_provincia_legacy = richiedente_provincia
    """)
