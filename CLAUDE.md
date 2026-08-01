# Repo: addons Odoo 19 — Misericordia Airola-Moiano

Note operative per sessioni future su questo repository, maturate durante
lo sviluppo del modulo `gestione_ass_volontariato` e dei moduli collegati.

## Struttura dei moduli custom

- **gestione_ass_volontariato** — modulo principale: interventi, richieste
  di assistenza, esercitazioni, turni, volontari (estensione hr.employee),
  automezzi (estensione fleet), dispositivi (estensione maintenance),
  contratti/assicurazioni, dashboard, gruppi di sicurezza
  (`group_volontariato_volontario`, `group_volontariato_responsabile`).
- **gestione_ass_volontariato_contabilita** — contabilità ETS (prima nota,
  rendiconto Mod. D), dipende da `gestione_ass_volontariato` + `account` +
  `analytic`. Menù "Contabilità" annidato sotto `menu_volontariato_root`.
- **gestione_ass_volontariato_presidi** — prestito presidi sanitari
  (donazioni, prestiti, magazzino), dipende da `gestione_ass_volontariato`.
  Menù "Prestito Presidi" annidato sotto `menu_volontariato_root`.
- **gestione_donatori** — anagrafica donatori e parametri donazione,
  modulo indipendente.

I moduli dipendenti possono referenziare i gruppi di sicurezza definiti in
`gestione_ass_volontariato` (es. `gestione_ass_volontariato.group_volontariato_responsabile`)
nei propri `groups="..."` sui menuitem, dato l'ordine di caricamento.

## Deploy: flusso e limitazioni note

1. Il sito (`misericordia.cloudpepper.site`) è collegato al branch **`main`**
   di questo repo tramite il pannello CloudPepper (Instances → Addons),
   pulsante **Update** per sincronizzare il codice.
2. Dopo "Update", su Odoo: Impostazioni → App → **Aggiorna** il modulo.
3. **Le modifiche ai soli file Python a volte non vengono ricaricate** dal
   processo Odoo già in esecuzione con il solo "Aggiorna" — serve anche il
   **Restart** del sito da CloudPepper (pulsante accanto a "Stop"). Le
   modifiche a XML/CSV/dati normalmente non richiedono il restart.
4. **La creazione di pull request tramite l'API/UI di GitHub in questo
   ambiente può fallire con errori 500** in modo persistente (non sempre
   transitorio). Se succede ripetutamente, con il consenso esplicito
   dell'utente si può pushare direttamente su `main` (fast-forward, mai
   force-push) invece di passare da una PR — verificare sempre prima con
   `git fetch origin main && git merge-base --is-ancestor origin/main HEAD`
   per assicurarsi che non ci siano divergenze, ed eventualmente fare
   `git rebase origin/main` se un'altra sessione ha pushato nel frattempo
   (può succedere: più sessioni Claude Code lavorano su moduli diversi
   dello stesso repo).
5. I commit di questa sessione risultano talvolta segnalati "Unverified"
   da un hook locale (`stop-hook-git-check.sh`) per mancanza di
   `gpg.ssh.allowedSignersFile` nel sandbox — è un **falso positivo di
   verifica locale**: i commit hanno comunque autore/committer corretto
   (`noreply@anthropic.com`) e firma SSH incorporata (verificabile con
   `git cat-file commit <sha>`, si vede il blocco `gpgsig`). Non riscrivere
   commit già pushati su `main` per questo motivo.

## Odoo 19 su questa istanza: differenze rispetto a versioni precedenti

Verificate una per una durante il debug (fonte: sorgente ufficiale
`github.com/odoo/odoo`, branch `19.0`), causa di diversi ParseError/
ValueError in fase di aggiornamento modulo:

- `res.groups.category_id` **non esiste più** (sostituito da un sistema
  di "privilege" via `res.groups.privilege_id` / `res.groups.privilege`,
  non ancora esplorato in dettaglio). Non impostare `category_id` sui
  gruppi custom.
- `res.groups.users` → rinominato **`res.groups.user_ids`**.
- `ir.ui.view.groups_id` → rinominato **`ir.ui.view.group_ids`**.
- `ir.ui.menu.groups_id` → rinominato **`ir.ui.menu.group_ids`** (ma la
  sintassi XML `<menuitem groups="...">` continua a funzionare invariata:
  la traduzione al nome campo corretto è gestita internamente da
  `convert.py`, quindi per i menuitem non serve preoccuparsene).
- Il modello ridotto `hr.employee.public` (usato per gli utenti senza
  `hr.group_hr_user`) espone solo un elenco fisso di campi dichiarati
  esplicitamente sulla sua classe Python — **non** un passthrough
  dinamico di tutti i campi di `hr.employee`. Campi custom aggiunti a
  `hr.employee` NON sono automaticamente disponibili lì. Se un campo
  custom stored viene "spazzato dentro" a un prefetch generico (es. da
  `res.partner.get_worklocation`/`get_attendee_detail` chiamati dal
  Calendario, che accedono a *qualsiasi* campo di `hr.employee` come
  `user_id` scatenando un prefetch collettivo), scatta un AccessError per
  gli utenti senza accesso HR completo. Fix: `prefetch=False` sui campi
  custom sensibili (restano leggibili se richiesti esplicitamente dalle
  viste, ma non finiscono più nei prefetch bulk non correlati).

## Pattern di sicurezza/permessi che FUNZIONANO su questa istanza

- **Nascondere un menu a un gruppo specifico, lasciandolo visibile a
  tutti gli altri**: `<menuitem groups="modulo.nome_gruppo"/>` (whitelist
  positiva). Impossibile escludere *solo* un sottogruppo da un menu
  altrimenti aperto a tutti senza introdurre un gruppo positivo che
  copre "tutti tranne quel sottogruppo" — per questo esiste
  `group_volontariato_responsabile`, a cui vanno aggiunti manualmente
  tutti gli utenti che devono mantenere l'accesso pieno.
- **Nascondere un singolo elemento (bottone/campo) a un gruppo
  specifico**, lasciandolo visibile a tutti gli altri, **in un'unica
  vista condivisa**: `groups="!modulo.nome_gruppo"` (prefisso `!` per
  l'esclusione) direttamente sull'elemento XML — confermato sicuro e
  funzionante (usato per nascondere "Aggiungi a Calendario" al ruolo
  Volontario sul form Turno).
- **Restringere create/write/unlink per un gruppo specifico** mantenendo
  la lettura aperta a tutti: righe multiple in `ir.model.access.csv` sullo
  stesso modello (una per `base.group_user` con `perm_read=1` e gli altri
  a 0, una per il gruppo con accesso pieno con tutti i perm a 1). Questo
  È il modo corretto/affidabile per rendere un modello "sola lettura" per
  un ruolo — **non** usare viste alternative "primary" con `priority`
  più basso per differenziare per gruppo.

## Pattern che NON funzionano (verificato sul campo)

- **Vista `ir.ui.view` con `inherit_id` + `group_ids` per mostrare una
  variante "sola lettura" a un gruppo specifico**: richiede `mode="primary"`
  (altrimenti Odoo rifiuta con "Inherited view cannot have 'groups' defined
  on the record"), ma anche con `mode="primary"` + `priority` più basso
  della vista di default, **gli utenti con privilegi elevati (Amministratore)
  bypassano il filtro per gruppo** nella selezione della vista di default
  (`ir.ui.view.default_view()`), quindi vedono comunque la vista con
  priorità più bassa **indipendentemente dal proprio gruppo** — bug
  riscontrato concretamente (l'admin perdeva il pulsante "Nuovo" destinato
  solo al ruolo Volontario). Usare invece la restrizione ACL descritta
  sopra, o - per un singolo elemento in una vista condivisa - `groups="!..."`.
- **Campo `domain` di un `ir.actions.act_window` scritto come testo
  semplice contenente `ref(...)`**: `ref()` è disponibile solo con
  l'attributo `eval="..."` (valutato in fase di caricamento dati), non
  come testo letterale del campo — altrimenti resta salvata la stringa
  `"ref(...)"` e il client JS fallisce con `EvalError: Name 'ref' is not
  defined` al momento di aprire l'azione.
- **Assumere che un `groups`/campo esista invariato da versioni Odoo
  precedenti**: verificare sempre sul sorgente ufficiale
  (`raw.githubusercontent.com/odoo/odoo/19.0/...` via WebFetch, o
  `mcp__github__search_code` con `repo:odoo/odoo`) prima di scrivere XML
  che referenzia campi su modelli core (`res.groups`, `ir.ui.view`,
  `ir.ui.menu`, `hr.employee`, ecc.) — in questa versione diversi nomi
  sono cambiati rispetto a quanto ci si aspetterebbe da versioni precedenti.

## Migrazioni dati

Quando si cambia il tipo di un campo già in produzione con dati reali
(es. `fields.Text` → `fields.Html`), aggiungere uno script
`migrations/<versione>/post-migration.py` che converte i valori esistenti
(escaping HTML + `\n` → `<br/>`) — altrimenti il testo esistente,
reinterpretato come HTML, perde gli a capo e rischia di rompersi se
contiene caratteri come `<`/`>`/`&`. Pattern già usato più volte in questo
repo, vedi `gestione_ass_volontariato/migrations/19.0.2.11.0/` e
`19.0.2.12.0/` come esempio.
