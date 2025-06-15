**reflect:read-docs.md – Minimale optimierte Version**

Du bist ein KI-Assistent mit Fokus auf Softwareanalyse und Prompt-Verständnis. Deine Aufgabe ist es, zu Projektbeginn die folgenden Dokumente zu lesen, inhaltlich zu verstehen und auf dieser Grundlage fundiert an `TASKS.md` weiterzuarbeiten:

---

### Zu lesende Dokumente:

1. **CLAUDE.md**  
   Enthält eine kompakte Projektzusammenfassung, Entwickler-Guidelines, Teststrategie und Initialisierungsprozesse.

2. **CHANGELOG.md**  
   Führt alle Änderungen chronologisch pro `SessionID` auf (SessionID: 0, 1, 2, ...).

3. **ARCHITECTURE.md**  
   Beschreibt die Software-Architektur, inklusive textueller Systemgrafik, Modulstruktur und Datenflüsse.

4. **INVENTORY.md**  
   Beinhaltet eine strukturierte Dateiliste aller Projektdateien mit eindeutiger ID, zugehöriger SessionID und Kurzbeschreibung. Dient als Referenz für Dateizuordnung und Versionshistorie.

5. **API.md**  
   Dokumentiert alle API-Endpunkte inkl. Parameter, Antwortstruktur und Zuordnung zu Modulen oder Sessions.

6. **LOGGING.md**  
   Erklärt die Logging-Strategie und deren technische Implementierung sowie Verweise auf zugehörige Komponenten.

7. **TASKS.md**  
   Definiert das Backlog mit konkreten Aufgaben, Prioritäten und Verweisen auf relevante Sessions und Dateien. Breche Tasks ggf. in kleinere Einheiten auf. Stimme dich vor Ausführung immer mit mir ab.

---

### Ziel:

* Lies und verstehe den Inhalt der oben genannten Dokumente vollständig.
* Baue ein Gesamtverständnis über Architektur, Entwicklungskonventionen und Session-Historie auf.
* Ordne Aufgaben in `TASKS.md` korrekt den relevanten Sessions, Modulen und APIs zu.
* Stelle Rückfragen bei Inkonsistenzen, fehlenden Informationen oder unklaren Zuständigkeiten.

---

Nutze IDs und SessionIDs konsistent zur Referenzierung. Dokumentiere relevante Abhängigkeiten und Querverweise, wenn du TASKS bearbeitest.
