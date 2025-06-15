## update.md – Dokumentation aktualisieren

### CLAUDE.md
Ergänzen, wenn sich Richtlinien, Teststrategien oder Initialisierungsprozesse geändert haben. Notiere sachlich alle relevanten Neuerungen (z. B. Build-Prozesse, Tooling, Onboarding-Abläufe).

### CHANGELOG.md
Füge einen neuen Eintrag zur aktuellen `SessionID` hinzu. Dokumentiere alle Änderungen (Features, Fixes, Strukturentscheidungen) stichpunktartig. Verlinke zu betroffenen Modulen, APIs, Logs und Aufgaben.

### ARCHITECTURE.md
Pflege Systemgrafik, Modulübersicht und Datenflüsse. Aktualisiere bei Einführung, Änderung oder Entfernung von Komponenten. Berücksichtige auch das Datenmodell. Entfernte Module sind auszutragen.

### SAD.md
Pflege alle technischen Aspekte der Systemausführung. Änderungen an Build-, Sync-, Bootstrap-, CLI- oder Deployment-Logik sind hier verbindlich zu dokumentieren.

### INVENTORY.md
Trage neu entstandene Dateien mit `ID`, `SessionID` und Beschreibung ein. Markiere veraltete Dateien als `deprecated` oder `removed`. Entfernte Dateien sind ebenfalls aus ARCHITECTURE.md, TASKS.md und ggf. API.md auszutragen.

### API.md
Ergänze neue oder geänderte Endpunkte. Verweise auf Parameter, Rückgaben, Zuständigkeiten und `SessionID`. Prüfe Konsistenz zur Architektur und verknüpfe mit Logikmodulen (ARCHITECTURE.md), Logs (LOGGING.md) und Aufgaben (TASKS.md).

### LOGGING.md
Dokumentiere neue oder angepasste Logs, Logging-Ebenen oder strukturelle Änderungen. Verlinke zu betroffenen Modulen (ARCHITECTURE.md), APIs (API.md) und Sessions (CHANGELOG.md).

### TASKS.md
Aktualisiere den Status bestehender Aufgaben (`done`, `ongoing`, `rejected`, etc.). Dokumentiere neue Folgeaufgaben – ggf. heruntergebrochen in Subtasks. Jede Aufgabe erhält eine Referenz zur `SessionID`, betroffenen Komponente und ggf. API/Modul/Log.

### TESTING.md
Aktualisiere bei neuen Testtools, Coverage-Regeln, Strategiewechseln oder Änderungen in Testdaten-Handling. Dokumentiere relevante Testfälle für neue APIs oder Module. Jeder neue Testpfad muss eindeutig zu SessionID und Modul rückverfolgbar sein.

---

## Vorgehensweise

### Änderungserfassung
- Erfasse alle Änderungen der letzten Session (Code, Struktur, Test, API, Logging, Dateien).
- Weise jeder Änderung eine eindeutige `SessionID` zu.

### Dokumentenpflege
- Aktualisiere die oben genannten Dokumente systematisch.
- Kurz, sachlich, vollständig – keine Marketingformulierungen.

### Konsistenzprüfung & Verknüpfungspflicht
- Ordne neue oder geänderte Dateien (`INVENTORY.md`) den richtigen Modulen (`ARCHITECTURE.md`) zu.
- Verlinke alle Änderungen im `CHANGELOG.md` mit zugehörigen APIs, Logs, Tasks und ggf. SAD.md.
- Prüfe, ob `CLAUDE.md`, `SAD.md` oder `TESTING.md` ergänzt werden müssen.
- Jede Änderung soll in mindestens drei Dokumenten nachvollziehbar sein:
  - Architektur oder Modulstruktur
  - Auswirkung (API, Log, Task, CHANGELOG)
  - Technische Ausführung (SAD.md, TESTING.md)

### Session-Metadatenprüfung
- Stelle sicher, dass jede Datei, API, Logikänderung und Aufgabe einer `SessionID` zugeordnet ist.
- Führe bei Bedarf eine Prüfung auf widersprüchliche oder fehlende Metadaten durch.

---

## Hinweise zur Bearbeitung

- IDs und SessionIDs sind konsistent zur Referenzierung zu verwenden
- Nutze strukturierte Formatierung zur Weiterverarbeitung durch Entwickler oder Analyse-Tools
- Verweise auf konkrete Dokumentstellen sind explizit zu machen, wenn möglich
- Ziel ist ein konsistenter, verwertbarer Überblick über die Projektstruktur mit klaren Handlungsempfehlungen


!!! MACHE GITPUSH NACH GITHUB ZUM SCHLUSS!!!
