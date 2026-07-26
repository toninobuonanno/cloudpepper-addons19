# -*- coding: utf-8 -*-


def _column_exists(cr, table, column):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (table, column))
    return bool(cr.fetchone())


def migrate(cr, version):
    """Precompila i nuovi campi obbligatori introdotti in questa versione.

    - donatori.donatore: Cognome/Nome, ricavati dal vecchio campo 'name'
      (Soggetto), che con questa versione diventa un campo calcolato.
    - donatori.parametro: donatore_id, ora obbligatorio. Gli eventuali
      parametri già registrati senza un donatore collegato vengono
      agganciati cercando un donatore con lo stesso nominativo, oppure
      (se non trovato) collegati a un nuovo donatore segnaposto creato
      dai dati già presenti sulla riga, per non perdere lo storico.
    """
    if not version:
        return

    if not _column_exists(cr, 'donatori_donatore', 'cognome'):
        cr.execute("""
            ALTER TABLE donatori_donatore
            ADD COLUMN IF NOT EXISTS cognome varchar,
            ADD COLUMN IF NOT EXISTS nome varchar
        """)

    # ── Parametri Donatori senza donatore_id (nuovo campo obbligatorio) ──
    if (_column_exists(cr, 'donatori_parametro', 'donatore_id')
            and _column_exists(cr, 'donatori_parametro', 'cognome')
            and _column_exists(cr, 'donatori_parametro', 'nome')):
        cr.execute("""
            SELECT id, cognome, nome, data_nascita
            FROM donatori_parametro
            WHERE donatore_id IS NULL
        """)
        for parametro_id, cognome, nome, data_nascita in cr.fetchall():
            full_name = ' '.join(p for p in (cognome, nome) if p).strip()
            donatore_id = None
            if full_name:
                cr.execute(
                    "SELECT id FROM donatori_donatore WHERE lower(name) = lower(%s)",
                    (full_name,),
                )
                matches = cr.fetchall()
                if len(matches) == 1:
                    donatore_id = matches[0][0]
            if donatore_id is None:
                cr.execute("""
                    INSERT INTO donatori_donatore (tessera_nazionale, name, active)
                    VALUES (%s, %s, true)
                    RETURNING id
                """, ('LEGACY-PARAM-%s' % parametro_id, full_name or 'Sconosciuto'))
                donatore_id = cr.fetchone()[0]
            cr.execute(
                "UPDATE donatori_parametro SET donatore_id = %s WHERE id = %s",
                (donatore_id, parametro_id),
            )

    # ── Cognome/Nome del donatore, ricavati dal vecchio 'name' (Soggetto) ──
    cr.execute("SELECT id, name FROM donatori_donatore WHERE cognome IS NULL")
    for donatore_id, name in cr.fetchall():
        parts = (name or '').split()
        if not parts:
            cognome, nome = 'Sconosciuto', 'Sconosciuto'
        elif len(parts) == 1:
            cognome, nome = parts[0], parts[0]
        else:
            cognome, nome = parts[0], ' '.join(parts[1:])
        cr.execute(
            "UPDATE donatori_donatore SET cognome = %s, nome = %s WHERE id = %s",
            (cognome, nome, donatore_id),
        )
