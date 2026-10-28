# -*- coding: utf-8 -*-

def _column_exists(cr, table, column):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (table, column))
    return bool(cr.fetchone())


def migrate(cr, version):
    """Assegna alla company originale (la più vecchia, cioè quella con id
    più basso) tutti i record creati prima dell'introduzione del campo
    company_id, in modo che non "scompaiano" dalla company a cui sono
    sempre appartenuti dopo l'attivazione del filtro multi-company.
    """
    if not version:
        return

    cr.execute("SELECT id FROM res_company ORDER BY id ASC LIMIT 1")
    row = cr.fetchone()
    if not row:
        return
    main_company_id = row[0]

    tables = [
        'volontariato_presidio',
        'volontariato_presidio_donazione',
        'volontariato_presidio_prestito',
    ]
    for table in tables:
        if not _column_exists(cr, table, 'company_id'):
            continue
        cr.execute(
            f"UPDATE {table} SET company_id = %s WHERE company_id IS NULL",
            (main_company_id,),
        )
