# 🚀 WINCASA Developer Quick Start

**Get coding in 2 minutes!**

## One-Command Setup

```bash
# Clone & Start (if not already done)
git clone [repository] && cd wincasa_llm

# Quick setup & launch
make setup && make dev
```

**Alternative if no make:**
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
./run_streamlit.sh
```

## ✅ What just happened?

1. **Virtual environment** created and activated
2. **Dependencies** installed (Streamlit, OpenAI, Firebird driver, etc.)
3. **Streamlit server** started on http://localhost:8667
4. **Database** ready (embedded Firebird)

## 🎯 First Steps

### 1. Test the UI
- Open: http://localhost:8667
- Select modes: `☑ UNIFIED` (recommended for new devs)
- Try query: **"Zeige alle Mieter"**
- See results in ~1-5ms

### 2. Understand the Architecture
```bash
# 5 Query Modes Available:
# 1-4: Legacy (JSON_VANILLA, JSON_SYSTEM, SQL_VANILLA, SQL_SYSTEM)  
# 5: UNIFIED (Phase 2 - intelligent routing)

# Test specific mode:
python debug_single_query.py "Alle Mieter" --mode=UNIFIED
```

### 3. Run Tests
```bash
make test              # Full test suite (26 tests)
make test-quick        # Quick subset  
make test-golden       # Test with real queries
```

## 🔧 Development Commands

```bash
./run_streamlit.sh --dev        # Start with verbose logging
./run_streamlit.sh --debug      # Start with debug instructions
./run_streamlit.sh --test       # Run tests before starting
./export_json.sh                # Export all SQL→JSON
python debug_single_query.py "Query" --compare  # Debug tool
```

## 🐛 Debug Your First Query

**Interactive Debugging:**
```bash
# Debug a specific query
python debug_single_query.py "Kaltmiete für FHALAMZIE" --mode=UNIFIED --trace

# Compare all modes  
python debug_single_query.py "Test query" --compare

# Start server in debug mode
./run_streamlit.sh --debug
```

**Manual Breakpoints:**
```python
# Add to any Python file:
import pdb; pdb.set_trace()
```

## 📁 Key Files to Know

| File | Purpose | Start Here If... |
|------|---------|------------------|
| `streamlit_app.py` | UI Entry Point | Working on frontend |
| `wincasa_query_engine.py` | Mode 5 Core Logic | Adding new features |
| `llm_handler.py` | Legacy Modes 1-4 | Fixing legacy issues |
| `layer4_json_loader.py` | Data Access | Working with JSON data |
| `test_suite_phase2.py` | Test Framework | Writing tests |

## 🚨 Common Issues

**Port already in use:**
```bash
./run_streamlit.sh --restart  # Kills existing processes
```

**API key missing:**
```bash
# Add to /home/envs/openai.env:
OPENAI_API_KEY=your_key_here
```

**Tests failing:**
```bash
make clean && make test-quick  # Reset and test core
```

## 📚 Next Steps

1. **Read Architecture:** [CLAUDE.md](CLAUDE.md) - Complete system overview
2. **Add Features:** [TASKS.md](tasks.md) - See current development tasks  
3. **Deep Dive:** [API.md](API.md) - Detailed API documentation

## 🎉 You're Ready!

- ✅ System running on http://localhost:8667
- ✅ Tests passing 
- ✅ Ready to develop

**Happy Coding!** 🚀

---

*Need help? Check [CLAUDE.md](CLAUDE.md) for detailed developer navigation.*