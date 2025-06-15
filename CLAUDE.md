CLAUDE.md – Dev Manual

## Projekt

WINCASA ist ein AI-powered Property Management Query System mit Dual-Engine Architecture. Das System bietet intelligentes Query-Routing zwischen 1-5ms Optimized Search, Template Engine (~100ms) und Legacy Fallback (500-2000ms). Eine Knowledge Base mit 226 automatisch extrahierten Field-Mappings ermöglicht Zero-Hardcoding für Business-SQL-Generierung. Production-ready mit 100% Test Coverage und Sphinx-Dokumentation.

Quick Start

source venv/bin/activate

./sync-project.sh

Code schreiben

./run-tests.sh

/commit → /gitpush

Entwicklungsregeln

1. Test First

Gegen echtes System

Keine Mocks, keine Test-DB

100 % Branch-Coverage

Neue Features: Test-First mit mindestens einem Happy-Path und Edge-Case

2. Log Everything

logging-Modul mit JSON-Format

Kein print() im Produktionscode

Kritische Pfade (Netzwerk, DB, Entscheidungen) immer mit Log-Eintrag

3. Commit Clean

Nur Conventional Commits

Format: type(scope): message

4. Dokumentation aktuell halten

Docstrings pflegen, Sphinx-Build muss sauber durchlaufen

5. Keine externe CI/CD

Lokaler Sync mit sync-project.sh

6. Spezialagenten nutzen

mcp-playwright → UI-Tests

mcp-context7 → Technologiedoku

mcp-zen → Debugging / Review

7. Jede Codedatei / Test / .py sollte maximal ~ 1500 token lang sein. Im Zweifel modularisier den Code weiter. Vergiss nicht zu dokumentieren.!

Vorgehen:

TASKS.md prüfen

Session

Task auswählen

Tests schreiben → Commit

Code schreiben → Commit

Docs aktualisieren → Commit

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