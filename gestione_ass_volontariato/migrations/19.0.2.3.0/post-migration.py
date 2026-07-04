# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def _column_exists(cr, table, column):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (table, column))
    return bool(cr.fetchone())


def migrate(cr, version):
    """Migra i dati esistenti del registro interventi.

    1. tipo_intervento (selection) -> tipo_intervento_id (Many2one)
    2. richiedente (char) -> richiedente_id (Many2one res.partner),
       creando i partner mancanti con città e provincia.
    """
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})

    # ── 1. Tipo Intervento ──────────────────────────────────────────
    if _column_exists(cr, 'volontariato_intervento', 'tipo_intervento'):
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
                    UPDATE volontariato_intervento
                    SET tipo_intervento_id = %s
                    WHERE tipo_intervento = %s
                      AND tipo_intervento_id IS NULL
                """, (tipo.id, old_val))

        # Eventuali valori non mappati -> "Altro" come fallback
        fallback = env.ref(
            'gestione_ass_volontariato.tipo_intervento_altro',
            raise_if_not_found=False,
        )
        if fallback:
            cr.execute("""
                UPDATE volontariato_intervento
                SET tipo_intervento_id = %s
                WHERE tipo_intervento_id IS NULL
            """, (fallback.id,))

    # ── 2. Richiedente -> res.partner ───────────────────────────────
    if _column_exists(cr, 'volontariato_intervento', 'richiedente'):
        cr.execute("""
            SELECT id, richiedente,
                   richiedente_citta_legacy,
                   richiedente_provincia_legacy
            FROM volontariato_intervento
            WHERE richiedente IS NOT NULL
              AND btrim(richiedente) != ''
              AND richiedente_id IS NULL
        """)
        rows = cr.fetchall()

        Partner = env['res.partner']
        State = env['res.country.state']
        italy = env.ref('base.it', raise_if_not_found=False)
        partner_cache = {}

        for intervento_id, nome, citta, provincia in rows:
            key = (nome.strip(), (citta or '').strip(), (provincia or '').strip())
            partner = partner_cache.get(key)
            if not partner:
                # Cerca un partner esistente con lo stesso nome
                partner = Partner.search([('name', '=', nome.strip())], limit=1)
                if not partner:
                    state = State
                    if provincia and italy:
                        state = State.search([
                            ('country_id', '=', italy.id),
                            '|',
                            ('name', '=ilike', provincia.strip()),
                            ('code', '=ilike', provincia.strip()),
                        ], limit=1)
                    partner = Partner.create({
                        'name': nome.strip(),
                        'city': (citta or '').strip() or False,
                        'state_id': state.id if state else False,
                        'country_id': italy.id if italy else False,
                        'is_company': True,
                    })
                partner_cache[key] = partner

            # Scrittura via ORM: aggiorna anche i related store
            # (richiedente_citta / richiedente_provincia)
            env['volontariato.intervento'].browse(intervento_id).write({
                'richiedente_id': partner.id,
            })

    # ── 3. Ricalcolo related per righe senza richiedente ────────────
    # (assicura coerenza dei campi store dopo il cambio di definizione)
    interventi = env['volontariato.intervento'].search([])
    env.add_to_compute(
        env['volontariato.intervento']._fields['richiedente_citta'], interventi
    )
    env.add_to_compute(
        env['volontariato.intervento']._fields['richiedente_provincia'], interventi
    )

    # ── 4. Pulizia colonne temporanee ───────────────────────────────
    cr.execute("""
        ALTER TABLE volontariato_intervento
        DROP COLUMN IF EXISTS richiedente_citta_legacy,
        DROP COLUMN IF EXISTS richiedente_provincia_legacy
    """)
