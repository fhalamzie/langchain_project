# WINCASA Code-Qualitätssicherung

Diese Dokumentation beschreibt die im WINCASA-Projekt verwendeten Tools und Standards zur Sicherstellung der Code-Qualität.

## Code-Qualitäts-Tools

Das WINCASA-Projekt verwendet ein umfassendes Set an Werkzeugen für automatisierte Code-Qualitätsprüfungen:

### Primäre Werkzeuge

- **Black**: Python-Code-Formatierer mit Zeilenlänge 88
  - Identifiziert Formatierungsprobleme (581 Probleme festgestellt, automatisch behebbar)
  - Sorgt für einheitlichen Codestil im gesamten Projekt

- **isort**: Import-Sortierung und -Organisation
  - Sortiert Importe nach Standardbibliotheken, Drittanbieterbibliotheken und projektinternen Modulen
  - Identifiziert Import-Sortierungsprobleme (7 Probleme gefunden, automatisch behebbar)

- **flake8**: Linting für Python-Code
  - Erkennt Stil- und Qualitätsprobleme (61 Stil-Probleme zur manuellen Prüfung)
  - Prüft PEP8-Konformität mit Ausnahmen für Firebird-SQL

- **bandit**: Sicherheitsprüfung für Python-Code
  - Identifiziert potenzielle Sicherheitsprobleme im Code
  - Fokus auf bekannte Schwachstellen und unsichere Praktiken

- **pytest-cov**: Code-Coverage-Analyse
  - Erstellt HTML-Reports der Testabdeckung
  - Identifiziert untestete Code-Bereiche

### Pre-Commit-Hooks

Das Projekt verwendet Pre-Commit-Hooks, um Qualitätsprüfungen vor jedem Commit automatisch durchzuführen:

```bash
# Pre-commit-Hooks einrichten
./run_tests.sh pre-commit
```

Die Konfiguration befindet sich in `.pre-commit-config.yaml` und umfasst:
- Automatische Black-Formatierung
- Import-Sortierung mit isort
- flake8-Prüfungen
- Bandit-Sicherheitsscans

## Qualitätsstandards

### Code-Struktur

- **Maximale Dateigröße**: 800 Zeilen pro .py-Datei
  - Bevorzugt 500 Zeilen für komplexe SQL-Logik
  - Unterstützt modulare Architektur und bessere Wartbarkeit

- **Modularer Aufbau**:
  - Klare Trennung zwischen Retrieval-Modi
  - Funktionale Separation der Komponenten

### Dokumentation im Code

- **Docstrings**: Jedes Modul beginnt mit einem aussagekräftigen Docstring
  - Google-Stil-Docstrings für SQL-Generierungsfunktionen obligatorisch
  - Klare Beschreibung des Zwecks und der Funktionalität

- **Typ-Hinweise**: Obligatorisch für alle neuen Funktionen, die mit LLM-Antworten arbeiten

### Namenskonventionen

- Bestehende Namenskonventionen aus `firebird_sql_agent_direct.py` und `enhanced_retrievers.py` folgen
- Konsistente Benennungsschemen für Klassen, Methoden und Variablen

## Code-Qualitätsprüfung ausführen

```bash
# Alle Tests und Qualitätsprüfungen ausführen
./run_tests.sh all

# Nur Code-Qualitätsprüfungen
./run_tests.sh lint

# Code automatisch formatieren
./run_tests.sh format-fix
```

## Kontinuierliche Verbesserung

- **Mindestanforderung**: 75% Testabdeckung für neue Module
- **Code-Reviews**: Vor jedem Merge in den Hauptzweig
- **Automatisierte Prüfungen**: Bei jedem Commit durch Pre-Commit-Hooks
- **Regelmäßige Refaktorisierungen**: Zur Reduzierung technischer Schulden

## Aktuelle Code-Qualitätsstatistik

- **Black**: 581 Formatierungsprobleme identifiziert (automatisch behebbar)
- **isort**: 7 Import-Sortierungen gefunden (automatisch behebbar)
- **flake8**: 61 Stil-Probleme zur manuellen Prüfung
- **bandit**: Sicherheitsprüfung bestanden
- **Testabdeckung**: 100% für Kernfunktionalität

---

Für mehr Informationen zu Entwicklungsrichtlinien und -workflows siehe [development-guidelines.md](development-guidelines.md).