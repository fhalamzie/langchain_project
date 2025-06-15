## cleanup.md – Code-Aufräumen und Legacy-Migration

Diese Anweisung dient dazu, eine unstrukturierte oder historisch gewachsene Codebasis auf ein neues, systematisch gepflegtes Dokumentationsmodell umzustellen. Ziel ist es, ein `CLEANUP_INVENTORY.md` zu erstellen, das die Grundlage für eine spätere `INVENTORY.md` bildet und den Übergang zur dokumentierten Projektstruktur unterstützt.

---

## Hintergrund

Viele Codebasen wachsen über Jahre, ohne konsistente Dokumentation oder klare Zuständigkeiten. Diese Migration führt ein Inventarisierungsschema ein, das aus dem bestehenden Code automatisiert oder halbautomatisiert erstellt wird. Es bildet die Brücke zwischen Bestandsanalyse und dokumentationsbasierter Weiterentwicklung.

---

## Schritte zur Migration

### 1. Codebestand erfassen

- Durchsuche alle relevanten Verzeichnisse rekursiv
- Identifiziere:
  - Dateien (Quellcode, Konfig, Skripte)
  - Module und Funktionen
  - Hilfs- und Build-Strukturen
  - Unverwendete, duplizierte oder veraltete Artefakte

### 2. Erstelle ein temporäres `CLEANUP_INVENTORY.md`

Für jede Einheit:

```markdown
- ID: relativer/pfad/zur/datei
  Typ: Datei | Funktion | Modul | Abhängigkeit
  Status: active | unused | deprecated | refactor-needed
  Begründung: Warum diese Einstufung?
  Empfehlung: löschen | dokumentieren | refactor | verschieben
  SessionID: <SessionReferenz, wenn anwendbar>
```

> Hinweis: Dieses Format dient als Vorbereitung für die Einführung eines vollständigen `INVENTORY.md` mit Querverlinkungen zur Architektur und CHANGELOG.

### 3. Optional: Übergabe an TASKS.md

- Generiere aus `CLEANUP_INVENTORY.md` strukturierte Tasks
- Jeder Eintrag mit `refactor-needed`, `deprecated`, `unused` wird in konkrete Aufgaben überführt
- Referenziere den ursprünglichen Pfad und die zugehörige Empfehlung

---

## Ergebnis

Ein maschinenlesbares Aufräuminventar (`CLEANUP_INVENTORY.md`), das als Migrationsbasis für zukünftige Dokumentationsprozesse dient – insbesondere die Einführung von `INVENTORY.md`, `ARCHITECTURE.md`, `CHANGELOG.md` und `TASKS.md`.

---

## Hinweise für das LLM

- Schreibe nachvollziehbar, ohne Automatisierungsfantasien
- Verwende real vorhandene Dateien und Strukturen
- Vermeide Doppeleinträge
- Nutze `SessionID` nur, wenn Kontextinformationen vorliegen
- Dokumentiere jede Annahme oder Entscheidung transparent

---

## Verknüpfungen zu Kerndokumenten

Um den späteren Übergang zu einem konsistenten, verknüpften Dokumentationssystem zu unterstützen, sind folgende Beziehungsverknüpfungen zu berücksichtigen:

- [ARCHITECTURE.md]: Weist Module aus, denen Dateien in `CLEANUP_INVENTORY.md` zugeordnet werden sollten.
- [SAD.md]: Gibt an, welche Dateien zur Laufzeitkritik und technischen Steuerung gehören.
- [CHANGELOG.md]: Alle lösch-, Refactor- oder Umbauvorschläge müssen im Session-Kontext nachvollziehbar dokumentiert werden.
- [INVENTORY.md]: Finalisierung des bereinigten `CLEANUP_INVENTORY.md` mit dauerhaften Metadaten.
- [TASKS.md]: Automatisierte Ableitung von Aufgaben für Refactoring, Migration oder Löschung.
- [CLAUDE.md]: Wenn bei der Aufräumung neue Richtlinien, Bootstrap-Abläufe oder Tools eingeführt werden, müssen diese dort reflektiert werden.
- [LOGGING.md]: Wenn Logging-relevante Dateien betroffen sind, Prüfung auf Logging-Konformität und Anpassung.
- [TESTING.md]: Bei kritischen Komponenten Prüfung, ob Tests vorhanden sind oder angelegt werden müssen.
- [API.md]: API-nahe Dateien oder Serverkomponenten prüfen, ob Änderungen an Endpunkten notwendig sind.

Ziel ist ein integratives, nachvollziehbares und automatisch nutzbares Inventar über alle Kernbereiche des Systems.

