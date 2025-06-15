Diese Anweisung dient dazu, eine unstrukturierte oder historisch gewachsene Codebasis auf ein neues, systematisch gepflegtes Dokumentationsmodell umzustellen. Ziel ist es, ein `CLEANUP_INVENTORY.md` zu erstellen, das die Grundlage für eine spätere `INVENTORY.md` bildet und den Übergang zur dokumentierten Projektstruktur unterstützt.

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
