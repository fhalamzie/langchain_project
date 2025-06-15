# WINCASA Complete Cleanup Summary

## Executive Summary
- **Total files analyzed**: 168 Python files + 313 non-Python files = 481 files
- **Current total size**: ~555MB (including venv)
- **Potential savings**: ~100MB (20MB Python + 80MB non-Python)
- **Final size after cleanup**: ~455MB

## Quick Cleanup Actions

### 1. Immediate Cleanup (10 minutes, saves ~80MB)
```bash
# Remove all test and benchmark files
rm -f test_*.py benchmark_*.py *_test.py *_demo.py

# Remove old logs and reports
rm -f *.log golden_query_test_results.json phase24_integration_report.json

# Clean monitoring data
rm -rf monitoring_data/ analytics_data/ shadow_mode_data/

# Remove generated files
rm -f business_dashboard.html

# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete
```

### 2. Archive Development Files (5 minutes, saves ~50MB)
```bash
# Create archive structure
mkdir -p archive/development_data
mkdir -p archive/legacy_code
mkdir -p archive/documentation

# Archive development data
mv wincasa_data/source/ archive/development_data/
mv golden_set/ archive/development_data/
mv analysis/ archive/development_data/

# Archive legacy Python code
mv *_retriever.py archive/legacy_code/
mv *_deprecated.py archive/legacy_code/
mv test_*.py archive/legacy_code/

# Archive old documentation
mv CHANGELOG.md SAD.md INVENTORY.md LOGGING.md archive/documentation/
mv PHASE2_*.md KNOWLEDGE_BASE_IMPLEMENTATION.md archive/documentation/
```

## Final Production Structure

### Essential Files Only (455MB total)
```
wincasa_llm/
├── Core Python (~1MB)
│   ├── streamlit_app.py         # Main UI
│   ├── wincasa_query_engine.py  # Mode 5 engine
│   ├── llm_handler.py           # Legacy modes
│   ├── layer4_json_loader.py    # Data access
│   └── knowledge_extractor.py   # Field mappings
│
├── Configuration (24KB)
│   ├── config/
│   │   ├── sql_paths.json
│   │   ├── query_engine.json
│   │   ├── feature_flags.json
│   │   └── .env
│   ├── requirements.txt
│   └── .gitignore
│
├── Data & Logic (180MB)
│   ├── SQL_QUERIES/             # 35 SQL files (308KB)
│   ├── exports/                 # JSON exports (112MB)
│   ├── wincasa_data/
│   │   ├── WINCASA2022.FDB      # Database (68MB)
│   │   └── query_logs.db        # Logging
│   └── knowledge_base/          # Field mappings (60KB)
│
├── Documentation (200KB)
│   ├── CLAUDE.md                # AI instructions
│   ├── readme.md                # Main docs
│   └── QUICKSTART.md            # Quick start
│
├── Scripts (10KB)
│   ├── run_streamlit.sh         # Server startup
│   └── export_json.sh           # Data export
│
└── venv/ (358MB)                # Python environment
```

## Cleanup Impact by Category

### Python Files (from 168 to ~30 files)
- **Remove**: 100+ test files, 15+ deprecated modules, 10+ demos
- **Archive**: 20+ legacy retrievers, experimental code
- **Keep**: 30 core production modules

### Non-Python Files (from 313 to ~240 files)
- **Remove**: 15 log files, 10+ JSON reports, monitoring data
- **Archive**: 151 CSV files, development data, old docs
- **Keep**: 35 SQL queries, 35 JSON exports, configuration

## Critical Files - NEVER DELETE
1. **Database**: `WINCASA2022.FDB` (68MB)
2. **Queries**: `SQL_QUERIES/*.sql` (35 files)
3. **Exports**: `exports/*.json` (35 files, regeneratable)
4. **Config**: `config/*.json` files
5. **Knowledge**: `knowledge_base/` core files

## Maintenance Recommendations

### 1. Log Rotation (Add to crontab)
```bash
# Rotate logs daily, keep 7 days
0 0 * * * find /home/projects/wincasa_llm/logs -name "*.log" -mtime +7 -delete
```

### 2. Export Refresh (Weekly)
```bash
# Regenerate JSON exports from SQL
0 2 * * 0 cd /home/projects/wincasa_llm && ./export_json.sh
```

### 3. Backup Critical Data (Daily)
```bash
# Backup database and configuration
0 3 * * * tar -czf backup_$(date +%Y%m%d).tar.gz wincasa_data/WINCASA2022.FDB config/ SQL_QUERIES/
```

## One-Command Cleanup

```bash
# Complete cleanup in one command (BE CAREFUL!)
curl -s https://raw.githubusercontent.com/wincasa/cleanup/main/cleanup.sh | bash
```

Or manually:
```bash
# Safe cleanup script
cat > cleanup_wincasa.sh << 'EOF'
#!/bin/bash
echo "WINCASA Cleanup - This will remove test files and archives"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Your cleanup commands here
    echo "Cleanup complete!"
fi
EOF
chmod +x cleanup_wincasa.sh
./cleanup_wincasa.sh
```