CLAUDE.md – Dev Manual

## Projekt

WINCASA ist ein AI-powered Property Management Query System mit Dual-Engine Architecture. Das System bietet intelligentes Query-Routing zwischen 1-5ms Optimized Search, Template Engine (~100ms), Legacy Fallback (500-2000ms) und neu Mode 6: Semantic Template Engine (~50ms). Eine Knowledge Base mit 400+ automatisch extrahierten Field-Mappings und 41 German Business Terms ermöglicht Zero-Hardcoding für Business-SQL-Generierung. Production-ready mit 100% Test Coverage und Sphinx-Dokumentation.

Quick Start

source venv/bin/activate

export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

./tools/scripts/sync-project.sh

# Server Management (Mit PM2 für besseres Logging)
./tools/scripts/pm2-wincasa.sh start    # Server starten
./tools/scripts/pm2-wincasa.sh status   # Status anzeigen
./tools/scripts/pm2-wincasa.sh logs     # Live-Logs streamen
./tools/scripts/pm2-wincasa.sh restart  # Server neustarten
./tools/scripts/pm2-wincasa.sh stop     # Server stoppen

# PM2 Monitoring
pm2 monit                              # Live Dashboard
pm2 logs wincasa --lines 100           # Letzte 100 Log-Zeilen

Code schreiben

./tools/scripts/run-tests.sh

/commit → /gitpush

Entwicklungsregeln

1. Test First

**Testpyramide**: Unit → Integration → E2E → Pipeline
- Unit Tests: src/wincasa/* modules mit pytest
- Integration Tests: tests/integration/ gegen echtes System  
- E2E Tests: tests/e2e/ mit Playwright UI-Automation
- Pipeline Tests: tests/pipeline/ für SAD-System-Validierung

100 % Branch-Coverage für Core-Module

Neue Features: Test-First mit Happy-Path, Edge-Case und E2E-Validation

2. Log Everything

logging-Modul mit JSON-Format

Kein print() im Produktionscode

Kritische Pfade (Netzwerk, DB, Entscheidungen) immer mit Log-Eintrag

3. Commit Clean

Nur Conventional Commits

Format: type(scope): message

4. Dokumentation aktuell halten

Docstrings pflegen, Sphinx-Build muss sauber durchlaufen

Live-Dokumentation für Entwicklung: ./docs-live.sh

5. Keine externe CI/CD

Lokaler Sync mit sync-project.sh

6. Spezialagenten nutzen

mcp-playwright → UI-Tests

mcp-context7 → Technologiedoku

mcp-zen → Debugging / Review

7. Jede Codedatei / Test / .py sollte maximal ~ 1500 token lang sein. Im Zweifel modularisier den Code weiter. Vergiss nicht zu dokumentieren.!

8. Server Management

IMPORTANT: Verwende IMMER `./tools/scripts/pm2-wincasa.sh` für Server-Operationen!
- PM2 Process Manager mit exzellentem Logging
- PYTHONUNBUFFERED=1 für sofortige Python-Logs
- Automatisches Restart bei Crashes mit Backoff
- Logs mit Timestamps in logs/pm2/
- Live-Monitoring mit `pm2 monit`
- Farbige Log-Ausgabe mit `./tools/scripts/pm2-wincasa.sh logs`

Vorgehen:

TASKS.md prüfen

Session

Task auswählen

Tests schreiben → Commit

Code schreiben → Commit

Docs aktualisieren (./update-docs.sh) → Commit

Push als Backup

Ende

Tests grün

Sphinx sauber

CHANGELOG.md aktuell

Push

Tools & Scripts

sync-project.sh: Self-Updating Stack Sync (SAD.md)

update-docs.sh: Sphinx Documentation Update

run-tests.sh: pytest mit Coverage

sphinx-autobuild: Live-Doku im Browser

pm2-wincasa.sh: Server-Management mit PM2 (besseres Logging)

Dokumente

SAD.md: Self-Updating Stack Architektur

ARCHITECTURE.md: Modulstruktur & Flows

LOGGING.md: Logging-Richtlinien

TESTING.md: Teststrategie & Tools

INVENTORY.md: Dateiübersicht

CHANGELOG.md: Änderungsverlauf

TASKS.md: Aufgaben und Session-Tracking


Command-Dokumente

.claude/commands/init.md: Session-Initialisierung

.claude/commands/analyze.md: Projekt-Analyse und Review

.claude/commands/cleanup.md: Code-Aufräumen und Legacy-Migration

.claude/commands/reflect.md: CLAUDE.md Meta-Verbesserung

.claude/commands/update.md: Dokumentation aktualisieren