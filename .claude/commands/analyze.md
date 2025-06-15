## analyze.md – Projekt-Analyse und Review

### SAD.md – System Architecture Document
Technische Umsetzung des Self-Updating Stacks. Enthält Build-, Sync- und Umschaltmechanismen für Konfiguration, Schema, Code-Generierung und Deployment. Verbindlich für alle Claude-gesteuerten Systemaktionen. Grundlage für reale Systemausführung.

### ARCHITECTURE.md
High-Level-Modulübersicht, Komponentenstruktur und Datenflüsse. Beschreibt die konzeptionelle Struktur, Modularisierung und Abhängigkeiten. Dient der semantischen Einordnung einzelner Module, Schnittstellen und Flows. Referenz für Refactoring oder Erweiterung.

### LOGGING.md
Legt Logging-Standards fest: Format, Fehlerklassifikation, Trace-ID-Konventionen, Umfang pro Ebene. Unverzichtbar für Debugging, Reviews und reproduzierbare Fehleranalysen.

### TESTING.md
Testarten, Tools (z. B. pytest, factory_boy), Coverage-Anforderungen. Legt fest, dass gegen das reale System getestet wird (nicht gegen Mocks). Beinhaltet Test-Datenstrategie und Reset-Mechanik.

### INVENTORY.md
Projektdateien mit IDs, Rollen, Dateitypen, Session-Zuordnung und Änderungsverläufen. Unterstützt Navigation und Code-Verständnis durch strukturierte Indexierung.

### CHANGELOG.md
Verlauf aller Features, Fixes und Strukturänderungen. Automatisch gepflegt über Commit-Metadaten. Wird bei jeder Claude-Session aktualisiert. Bindeglied zu TASKS.md, API.md und INVENTORY.md.

### TASKS.md
Strukturierte Aufgaben- und Backlog-Verwaltung. Beinhaltet Rückverweise auf Sessions, Commits und Zielsetzungen. Steuerdatei für Claude CLI.

### API.md
Spezifikation aller HTTP-Endpunkte, Request-Formate, Parameter, Rückgaben, Statuscodes. Dient sowohl Claude als auch Menschen zur API-Nutzung. Aktualisiert sich über Docstrings, nicht manuell.

---

## Zielsetzung

- Erkenne Inkonsistenzen, Redundanzen oder Lücken zwischen den acht Kerndokumenten
- Ermittle fehlende oder veraltete Informationen (z. B. unvollständige API-Doku, fehlende Logreferenzen)
- Schlage konkrete Verbesserungen für Struktur, Inhalt und Prozessintegration vor
- Verknüpfe alle acht Kerndokumente konsistent miteinander, inkl. technischer Umsetzung (SAD.md), Architektur, Logging, Tests, API, Aufgaben und Änderungsverläufe
- Ermögliche automatisierbare Ableitungen für Tests, Dokumentationspflege und Deployment

---

## Vorgehen

### Analysephase

- Lese alle acht Kerndokumente systematisch ein
- Identifiziere pro SessionID relevante Einträge (CHANGELOG, INVENTORY, API, LOGGING)
- Mache Diskrepanzen sichtbar (z. B. API-Endpunkt ohne Modul, Datei ohne Beschreibung, Änderung ohne Logbezug)

### Verknüpfungsphase

- Ordne INVENTORY-Dateien den ARCHITECTURE-Komponenten zu
- Verlinke CHANGELOG-Einträge mit API-Dokumentation, Loggingpunkten, SAD.md und CLAUDE.md
- Integriere SAD.md explizit als verbindliche Quelle für technische Umsetzung
- Erstelle eine Liste von Sessions mit fehlenden oder widersprüchlichen Metadaten

### Auswertungsphase

- Generiere strukturierte Verbesserungsvorschläge:
  - Dokumentation (Ergänzungen, Vereinheitlichungen)
  - Technische Schulden (z. B. fehlende Tests, ungenutzte Module)
  - Onboarding-Prozesse (z. B. unvollständige Bootstrap-Anleitungen)
  - Logging- und Monitoring-Lücken

---

## Format der Analyseausgabe

### Hinweise zur Bearbeitung

- IDs und SessionIDs sind konsistent zur Referenzierung zu verwenden
- Nutze strukturierte Formatierung zur Weiterverarbeitung durch Entwickler oder Analyse-Tools
- Verweise auf konkrete Dokumentstellen sind explizit zu machen, wenn möglich
- Ziel ist ein konsistenter, verwertbarer Überblick über die Projektstruktur mit klaren Handlungsempfehlungen

