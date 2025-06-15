## init.md – Session-Initialisierung

Du bist ein KI-Assistent mit Fokus auf Softwareanalyse und Prompt-Verständnis. Deine Aufgabe ist es, zu Projektbeginn die folgenden Dokumente zu lesen, inhaltlich zu verstehen und auf dieser Grundlage fundiert an `TASKS.md` weiterzuarbeiten:

---

### Zu lesende Dokumente:

[SAD.md – System Architecture Document]

Technische Umsetzung des Self-Updating Stacks. Enthält Build-, Sync- und Umschaltmechanismen für Konfiguration, Schema, Code-Generierung und Deployment. Verbindlich für alle Claude-gesteuerten Systemaktionen.

[ARCHITECTURE.md]

High-Level-Modulübersicht, Komponentenstruktur und Datenflüsse. Dient der semantischen Einordnung einzelner Module, Schnittstellen und Flows. Referenzdokument für Refactoring oder konzeptionelle Erweiterungen.

[LOGGING.md]

Legt Logging-Standards fest: Format, Fehlerklassifikation, Trace-ID-Konventionen, Umfang pro Ebene. Unverzichtbar für Debugging, Reviews und reproduzierbare Fehleranalysen.

[TESTING.md]

Testarten, Tools (z. B. pytest, factory_boy), Coverage-Anforderungen. Legt fest, dass gegen das reale System getestet wird (nicht gegen Mocks). Beinhaltet auch Test-Datenstrategie und Reset-Mechanik.

[INVENTORY.md]

Projektdateien mit IDs, Rollen, Dateitypen, Session-Zuordnung und Änderungsverläufen. Unterstützt Navigation und Code-Verständnis durch strukturierte Indexierung.

[CHANGELOG.md]

Verlauf aller Features, Fixes und Strukturänderungen. Automatisch gepflegt über Commit-Metadaten. Wird bei jeder Claude-Session aktualisiert. Bindeglied zu TASKS.md und INVENTORY.md.

[TASKS.md]

Strukturierte Aufgaben- und Backlog-Verwaltung. Beinhaltet auch Rückverweise auf Sessions, Commits und motivierende Zielsetzungen. Wird als Steuerdatei für Claude CLI verwendet.

[API.md]

Spezifikation aller HTTP-Endpunkte, Request-Formate, Parameter, Rückgaben, Statuscodes. Dient sowohl Claude als auch Menschen zur Konsumierung der API-Schnittstellen. Aktualisiert sich über Docstrings, nicht manuell.
---

### Ziel:

* Lies und verstehe den Inhalt der oben genannten Dokumente vollständig.
* Baue ein Gesamtverständnis über Architektur, Entwicklungskonventionen und Session-Historie auf.
* Ordne Aufgaben in `TASKS.md` korrekt den relevanten Sessions, Modulen und APIs zu.
* Stelle Rückfragen bei Inkonsistenzen, fehlenden Informationen oder unklaren Zuständigkeiten.

---

Nutze IDs und SessionIDs konsistent zur Referenzierung. Dokumentiere relevante Abhängigkeiten und Querverweise, wenn du TASKS bearbeitest.
