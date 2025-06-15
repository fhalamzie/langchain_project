
Dokumente zur Analyse:

CLAUDE.md

Projektübersicht, Entwickler-Guidelines, Teststrategie, Initialisierungsprozesse

CHANGELOG.md

Änderungen pro Claude-Version, strukturiert nach SessionID (z. B. 0, 1, 2, ...)

ARCHITECTURE.md

Beschreibung der Softwarearchitektur, Systemgrafik, Komponenten, Datenflüsse, ggf. Datenmodell

INVENTORY.md

Strukturierte Auflistung aller Projektdateien mit ID, SessionID-Zuordnung und Kurzbeschreibung; dient als Referenz für Dateizuordnung und Versionshistorie

API.md

Listet alle API-Endpunkte inkl. Methoden, Parameter, Rückgaben und Modulbezug

LOGGING.md

Dokumentiert Logging-Strategie, technische Umsetzung, Referenzen auf konkrete Komponenten und Sessions

Zielsetzung

Erkenne Inkonsistenzen, Redundanzen oder Lücken zwischen den Dokumenten

Ermittle fehlende oder veraltete Informationen (z. B. unvollständige API-Doku, fehlende Logreferenzen)

Schlage konkrete Verbesserungen für Struktur, Inhalt und Prozessintegration vor

Verknüpfe Architektur, CHANGELOG, INVENTORY, APIs und Logs logisch miteinander

Ermögliche automatisierbare Ableitungen für Tests, Dokumentationspflege und Deployment

Vorgehen

Analysephase:

Lese alle sechs Dokumente systematisch ein

Identifiziere pro SessionID relevante Einträge (CHANGELOG + INVENTORY + API + LOGGING)

Mache Diskrepanzen sichtbar (z. B. API-Endpunkt ohne Modul, Datei ohne Beschreibung, Änderung ohne Logbezug)

Verknüpfungsphase:

Ordne INVENTORY-Dateien den ARCHITECTURE-Komponenten zu

Verlinke CHANGELOG-Einträge mit API-Dokumentation, Loggingpunkten und CLAUDE-Guidelines

Erstelle eine Liste von Sessions mit fehlenden oder widersprüchlichen Metadaten

Auswertungsphase:

Generiere strukturierte Verbesserungsvorschläge:

Dokumentation (Ergänzungen, Vereinheitlichungen)

Technische Schulden (z. B. fehlende Tests, ungenutzte Module)

Onboarding-Prozesse (z. B. unvollständige Bootstrap-Anleitungen)

Logging- und Monitoring-Lücken

Format der Analyseausgabe

Hinweise zur Bearbeitung

IDs und SessionIDs sind konsistent zur Referenzierung zu verwenden

Nutze strukturierte Formatierung zur Weiterverarbeitung durch Entwickler oder Analyse-Tools

Verweise auf konkrete Dokumentstellen sind explizit zu machen, wenn möglich

Ziel ist ein konsistenter, verwertbarer Überblick über die Projektstruktur mit klaren Handlungsempfehlungen

