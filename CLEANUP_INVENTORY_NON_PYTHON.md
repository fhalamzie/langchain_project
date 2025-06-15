# WINCASA Non-Python Files Cleanup Inventory

## Overview
- **Total non-Python files**: 313 files
- **Major categories**: CSV (151), JSON (66), SQL (42), MD (30), LOG (15), SH (2)
- **Total disk usage**: ~195MB (excluding venv)

## 1. Configuration Files

### Essential for Production
```
✅ config/sql_paths.json         # Core path configuration
✅ config/query_engine.json      # Query engine settings
✅ config/feature_flags.json     # Feature toggles
✅ config/.env                   # Environment variables
✅ .gitignore                    # Git configuration
✅ export_json.sh                # Data export script
✅ run_streamlit.sh              # Server startup script
```

### Can Be Archived/Removed
```
❌ config/development.json       # Development-only settings
❌ config/test.json             # Test configurations
```

## 2. Documentation Files (30 MD files)

### Essential for Production
```
✅ CLAUDE.md                     # AI assistant instructions
✅ readme.md                     # Main documentation
✅ QUICKSTART.md                 # Quick start guide
✅ ARCHITECTURE.md               # System architecture
✅ API.md                        # API documentation
```

### Development/Archive
```
📦 CHANGELOG.md                  # Historical changes
📦 SAD.md                        # Software architecture document
📦 INVENTORY.md                  # Old inventory
📦 CLEANUP_INVENTORY.md          # Python cleanup inventory
📦 LOGGING.md                    # Logging documentation
📦 PHASE2_FINAL_SUMMARY.md       # Phase 2 summary
📦 KNOWLEDGE_BASE_IMPLEMENTATION.md # KB implementation details
📦 tasks.md / TASKS.md           # Development tasks
```

## 3. Data Directories

### SQL_QUERIES/ (35 files, 308KB) - ESSENTIAL
```
✅ All 35 .sql files             # Core business queries
   - Define all system functionality
   - Required for JSON export generation
   - Source of truth for business logic
```

### exports/ (112MB) - PRODUCTION DATA
```
✅ 35 JSON export files          # Exported query results
✅ _export_summary.json          # Export metadata
✅ _verification_summary.json    # Data verification
✅ rag_data/                     # RAG-specific exports
   - MUST BE REGENERATED if SQL queries change
   - Contains 229,500 rows of business data
```

### wincasa_data/ (67MB) - MIXED
```
✅ WINCASA2022.FDB              # Production database (68MB)
✅ query_logs.db                 # Query logging database
❌ source/                      # Development data (can archive)
   - table_to_csv_with_top_50/  # 151 CSV files
   - schema/                    # Schema documentation
```

### knowledge_base/ (60KB) - ESSENTIAL
```
✅ business_vocabulary.json      # Field mappings
✅ alias_map.json                # Alias mappings
✅ join_graph.json               # Table relationships
❌ business_vocabulary_candidates.json # Development file
❌ extraction_report.txt         # One-time report
```

### golden_set/ (104KB) - TESTING
```
📦 queries.json                  # Test queries
📦 queries_complex.json          # Complex test cases
📦 queries_lookup.json           # Lookup test cases
📦 queries_template.json         # Template test cases
📦 baseline_results_*.json       # Test baselines
📦 summary.json                  # Test summary
```

## 4. Log Files (15 files, ~15MB)

### Active Logs (Keep Latest Only)
```
⚠️ logs/layer2.log              # Main app log (783KB)
⚠️ logs/layer2_api.log          # API log (13MB)
⚠️ logs/layer2_performance.log  # Performance log (811KB)
⚠️ logs/layer2_errors.log       # Error log (28KB)
⚠️ logs/query_paths.log         # Query routing (6KB)
⚠️ logs/benchmark.log           # Benchmarks (288B)
```

### Old Logs (Remove)
```
❌ streamlit.log                 # Old format
❌ streamlit_final.log           # Old session
❌ streamlit_fixed.log           # Old session
❌ json_export.log               # One-time export
❌ analytics_test.log            # Test log
❌ quick_test_results.log        # Test results
❌ golden_query_test_results.json # Test results
```

## 5. Generated/Temporary Files

### Can Be Removed
```
❌ business_dashboard.html       # Generated dashboard
❌ monitoring_data/*.json        # Monitoring snapshots
❌ analytics_data/*.json         # Analytics snapshots
❌ shadow_mode_data/*.json       # Shadow mode data
❌ phase24_integration_report.json # One-time report
```

### Database Views (Keep)
```
✅ database/views/*.sql          # 5 view definitions
✅ database/create_phase2_views.sql # View creation script
```

## 6. Cleanup Recommendations

### Immediate Actions (Save ~80MB)
```bash
# Remove old logs
rm -f *.log
rm -f golden_query_test_results.json
rm -f phase24_integration_report.json

# Clean monitoring data
rm -rf monitoring_data/
rm -rf analytics_data/
rm -rf shadow_mode_data/

# Remove generated files
rm -f business_dashboard.html
```

### Archive Development Data (Save ~30MB)
```bash
# Create archive
mkdir -p archive/development_data
mv wincasa_data/source/ archive/development_data/
mv golden_set/ archive/development_data/
mv knowledge_base/*_candidates.json archive/development_data/
mv knowledge_base/extraction_report.txt archive/development_data/
```

### Log Rotation Setup
```bash
# Add to crontab for production
# Rotate logs daily, keep 7 days
0 0 * * * find /home/projects/wincasa_llm/logs -name "*.log" -mtime +7 -delete
```

## 7. Production File Structure

### Final Essential Structure
```
wincasa_llm/
├── config/               # Configuration files
│   ├── sql_paths.json
│   ├── query_engine.json
│   ├── feature_flags.json
│   └── .env
├── SQL_QUERIES/          # 35 SQL query files
├── exports/              # JSON exports (regeneratable)
├── wincasa_data/
│   ├── WINCASA2022.FDB   # Production database
│   └── query_logs.db     # Query logging
├── knowledge_base/       # Field mappings
│   ├── business_vocabulary.json
│   ├── alias_map.json
│   └── join_graph.json
├── database/             # View definitions
│   └── views/
├── logs/                 # Active logs (auto-rotate)
├── CLAUDE.md            # AI instructions
├── readme.md            # Documentation
├── QUICKSTART.md        # Quick start
├── export_json.sh       # Export script
└── run_streamlit.sh     # Startup script
```

## 8. Additional Directories

### .claude/ Directory
```
📦 .claude/settings.local.json   # Local Claude settings
📦 .claude/commands/             # Claude command history
   - Development artifact, can be removed
```

### analysis/ Directory  
```
📦 sql_query_content_analysis.md # One-time analysis
   - Development documentation, can archive
```

### sql_templates/ Directory
```
❓ Currently empty (4KB)         # Check if needed
```

## 9. Storage Summary

### Current Usage
- Python files: ~2MB
- Non-Python files: ~195MB
- venv: 358MB
- **Total: ~555MB**

### After Cleanup
- Python files: ~1.5MB (after Python cleanup)
- Non-Python files: ~115MB (after this cleanup)
- venv: 358MB
- **Total: ~475MB** (80MB saved)

### Critical Files Never to Delete
1. `WINCASA2022.FDB` - Production database
2. `SQL_QUERIES/*.sql` - Business logic
3. `config/*.json` - System configuration
4. `knowledge_base/` core files - Field mappings
5. `exports/` - Can regenerate but needed for operation

## 10. Complete Cleanup Script

```bash
#!/bin/bash
# WINCASA Complete Cleanup Script

echo "Starting WINCASA cleanup..."

# 1. Remove old logs
echo "Removing old logs..."
rm -f *.log
rm -f golden_query_test_results.json
rm -f phase24_integration_report.json

# 2. Clean monitoring/analytics data
echo "Cleaning monitoring data..."
rm -rf monitoring_data/
rm -rf analytics_data/
rm -rf shadow_mode_data/

# 3. Remove generated files
echo "Removing generated files..."
rm -f business_dashboard.html

# 4. Archive development data
echo "Archiving development data..."
mkdir -p archive/development_data
mv -f wincasa_data/source/ archive/development_data/ 2>/dev/null
mv -f golden_set/ archive/development_data/ 2>/dev/null
mv -f knowledge_base/*_candidates.json archive/development_data/ 2>/dev/null
mv -f knowledge_base/extraction_report.txt archive/development_data/ 2>/dev/null
mv -f analysis/ archive/development_data/ 2>/dev/null

# 5. Archive old documentation
echo "Archiving old documentation..."
mkdir -p archive/documentation
mv -f CHANGELOG.md archive/documentation/ 2>/dev/null
mv -f SAD.md archive/documentation/ 2>/dev/null
mv -f INVENTORY.md archive/documentation/ 2>/dev/null
mv -f LOGGING.md archive/documentation/ 2>/dev/null
mv -f PHASE2_*.md archive/documentation/ 2>/dev/null
mv -f KNOWLEDGE_BASE_IMPLEMENTATION.md archive/documentation/ 2>/dev/null

# 6. Clean Claude directory
echo "Cleaning Claude directory..."
rm -rf .claude/

# 7. Clean empty directories
echo "Removing empty directories..."
find . -type d -empty -delete 2>/dev/null

# 8. Clear Python cache
echo "Clearing Python cache..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete

echo "Cleanup complete!"
echo "Run 'du -sh .' to see new size"
```