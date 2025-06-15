## Zu aktualisierende Dokumente

### CLAUDE.md
Ergänzen, wenn sich Richtlinien, Teststrategien oder Initialisierungsprozesse geändert haben. Notiere sachlich alle relevanten Neuerungen (z. B. Build-Prozesse, Tooling, Onboarding-Abläufe).

### CHANGELOG.md
Füge einen neuen Eintrag zur aktuellen `SessionID` hinzu. Dokumentiere alle Änderungen (Features, Fixes, Strukturentscheidungen) stichpunktartig.

### ARCHITECTURE.md
Pflege Systemgrafik, Modulübersicht und Datenflüsse. Aktualisiere bei Einführung, Änderung oder Entfernung von Komponenten. Berücksichtige auch das Datenmodell.

### INVENTORY.md
Trage neu entstandene Dateien mit `ID`, `SessionID` und Beschreibung ein. Markiere veraltete Dateien als `deprecated` oder `removed`.

### API.md
Ergänze neue oder geänderte Endpunkte. Verweise auf Parameter, Rückgaben, Zuständigkeiten und `SessionID`. Prüfe Konsistenz zur Architektur.

### LOGGING.md
Dokumentiere neue oder angepasste Logs, Logging-Ebenen oder strukturelle Änderungen. Verlinke zu Modulen, APIs und betroffenen Sessions.

### TASKS.md
Aktualisiere den Status bestehender Aufgaben (`done`, `ongoing`, `rejected`, etc.). Dokumentiere neu entstandene Folgeaufgaben – ggf. heruntergebrochen in Subtasks. Jede Aufgabe erhält eine Referenz zur `SessionID` und betroffenen Komponente.

---

## Vorgehensweise

### Änderungserfassung
- Erfasse alle Änderungen der letzten Session (Code, Struktur, Test, API, Logging, Dateien).
- Weise jeder Änderung eine eindeutige `SessionID` zu.

### Dokumentenpflege
- Aktualisiere die oben genannten Dokumente systematisch.
- Kurz, sachlich, vollständig – keine Marketingformulierungen.

### Konsistenzprüfung
- Ordne neue oder geänderte Dateien (`INVENTORY.md`) den richtigen Modulen (`ARCHITECTURE.md`) zu.
- Verlinke alle Änderungen im `CHANGELOG.md` mit zugehörigen APIs, Logs und betroffenen Tasks.
- Prüfe, ob `CLAUDE.md` ergänzt werden muss (z. B. bei Änderungen im Deployment- oder Testprozess).
