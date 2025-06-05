# WINCASA Entwicklungsrichtlinien

## Entwicklungs-Workflow

1. **Vorbereitende Recherche**: MCP Context7 für relevante Technologien und Frameworks konsultieren
2. **Code-Analyse**: Bestehenden Code analysieren, um Retrieval-Mode-Muster zu verstehen
3. **Test-First**: Tests für neue SQL-Agent-Funktionalität vor der Implementierung erstellen
4. **Feature-Implementierung**: Funktionen unter Einhaltung der bestehenden Firebird-Konventionen implementieren
5. **Testsuite ausführen**: Alle Retrieval-Modi testen und sicherstellen, dass sie bestanden werden
6. **Dokumentation aktualisieren**: task.md mit Fortschritt und Implementierungsdetails aktualisieren
7. **Commit mit klarer Nachricht**: Auf spezifische Komponenten verweisen
8. **Regelmäßig zu GitHub pushen**: Backup aufrechterhalten

## Dokumentationsrichtlinien

**WICHTIG:** Fokussierte und aktuelle Dokumentation pflegen:
- **claude.md & readme.md:** Nur für größere architektonische Änderungen aktualisieren
- **plan.md:** Übergeordnete Strategie und Entwicklungsphasen
- **tasks.md:** Detaillierte Implementierungsaufgaben und Fortschrittsverfolgung
- **Alle routinemäßigen Updates** gehören in plan.md oder tasks.md, nicht in claude.md/readme.md

## Codierungsstandards

- **Max. 800 Zeilen pro .py-Datei** (vorzugsweise 500 Zeilen für komplexe SQL-Logik)
- **Modulare Architektur** mit klarer Trennung zwischen Retrieval-Modi
- **Jedes Modul beginnt** mit aussagekräftigem Docstring, der den Zweck erklärt
- **Bestehende Muster verwenden** aus `firebird_sql_agent_direct.py` und `enhanced_retrievers.py`
- **Bestehende Code-Konventionen einhalten**, insbesondere für Firebird-SQL-Generierung

## Dateireferenzen

Immer auf spezifische Code-Stellen mit `file_path:line_number` für einfache Navigation verweisen.

## Kritische Systemdateien

- **SQL Agent Core:** `firebird_sql_agent_direct.py:1-800`
- **Retrieval System:** `enhanced_retrievers.py:1-600`
- **Database Interface:** `fdb_direct_interface.py:1-400`
- **LangChain Integration:** `langchain_sql_retriever_fixed.py:1-300`
- **Global Context:** `global_context.py:1-200`
- **Business Glossar:** `business_glossar.py:1-600`

## Umgebung & Konfiguration

- **Primäre Konfiguration:** Umgebungsvariablen in `/home/envs/`
- **API-Schlüssel-Speicherort:** `/home/envs/openai.env`, `/home/envs/openrouter.env`
- **Datenbank:** `WINCASA2022.FDB` (151 Tabellen, 517 Wohnungen, 698 Bewohner)
- **Firebird-Server:** Port 3050 für LangChain-Modus
- **Phoenix-Monitoring:** SQLite-Backend auf `localhost:6006`

## MCP Context7-Nutzung

**WICHTIG:** MCP Context7-Tools für Dokumentationsnachschlag VOR der Implementierung verwenden:
- **Zweck**: Nur für Dokumentationsnachschlag und Best-Practices-Recherche
- **Wann**: Vor Code-Änderungen, um Frameworks/Bibliotheken zu verstehen
- **Nicht für**: Tatsächliche Implementierung - nur zum Lernen und als Referenz
- **Beispiele**: LangChain-Muster, SQLAlchemy-Nutzung, pytest Best Practices

## Git & Commits

- **Regelmäßige Commits** mit aussagekräftigen Commit-Nachrichten im konventionellen Format
- **Dateispeicherorte referenzieren** mit dem Muster `file_path:line_number`
- **Zuerst lokal testen, dann committen** - keine Ausnahmen
- **Jede Änderung des Retrieval-Modus** erfordert einen eigenen Commit
- **task.md aktualisieren** für Fortschrittsverfolgung (NICHT claude.md, außer bei größeren architektonischen Änderungen)

## Sicherheitsrichtlinien

- **Datenbankzugriff:** Immer parametrisierte Abfragen für FDB-Operationen verwenden
- **API-Schlüssel:** Nur Umgebungsvariablen (`/home/envs/`), niemals im Code
- **Logging:** SQL-Verbindungszeichenfolgen bereinigen und Anmeldeinformationen entfernen
- **Fehlerbehandlung:** Internes Datenbankschema niemals Benutzern offenlegen

## Umgebungseinrichtung

```bash
# Schnellstart
git clone https://github.com/fhalamzie/langchain_project.git
cd langchain_project
pip install -r requirements.txt

# System starten
./start_enhanced_qa_direct.sh
```

## Entwicklungsbefehle

```bash
# Testen
./run_tests.sh test              # Alle Unit-Tests
python diagnostic_test.py       # Systemvalidierung

# Code-Qualität
./run_tests.sh format-fix        # Automatische Formatierung
./run_tests.sh lint             # Code-Qualität prüfen

# Monitoring
# Phoenix-Dashboard: http://localhost:6006
```

---

**Für detaillierte Implementierungsaufgaben und Fortschritte:** Siehe `tasks.md`  
**Für übergeordnete Strategie und Planung:** Siehe `plan.md`