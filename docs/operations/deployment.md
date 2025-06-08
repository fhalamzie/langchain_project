# Deployment Instructions for Claude AI

## Environment Setup

### 1. Required Environment File
Create `/home/envs/openai.env` with:
```bash
OPENAI_API_KEY=your_openai_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
```

### 2. Database Setup
```bash
# Start Firebird server
sudo systemctl start firebird

# Check status
sudo systemctl status firebird

# Verify database file permissions (CRITICAL)
sudo chgrp firebird WINCASA2022.FDB
sudo chmod 660 WINCASA2022.FDB
```

### 3. Python Environment
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Testing Commands

### Primary Verification
```bash
# ALWAYS run this first to verify all 9 modes
python quick_3question_benchmark_final.py

# Expected output:
# 🎯 Working Modes: 9/9
# ✅ Functional: Enhanced, Contextual Enhanced, Hybrid FAISS, Filtered LangChain, TAG Classifier, Smart Fallback, Smart Enhanced, Guided Agent, Contextual Vector
# 🎉 EXCELLENT! System ready for production!
```

### Additional Testing
```bash
# Comprehensive end-to-end testing
python comprehensive_endresults_test.py

# Performance benchmarking
python performance_benchmarking_suite.py

# Individual mode status check
python test_9_mode_status.py

# Real database results verification
python test_real_database_results.py
```

## Critical Connection Strings

### Database Connection Format
```python
# ALWAYS use this exact format (note the double slash)
db_connection = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
```

### LLM Configuration
```python
# Standard LLM setup
from gemini_llm import get_gemini_llm
llm = get_gemini_llm()
```

## Troubleshooting

### If Any Mode Fails:
1. Check environment variables: `cat /home/envs/openai.env`
2. Verify Firebird: `sudo systemctl status firebird`
3. Check database permissions: `ls -la WINCASA2022.FDB`
4. Test connection: `python -c "import sqlalchemy; print('OK')"`

### Common Issues:
- **Database locked**: Restart Firebird service
- **Permission denied**: Fix file permissions with chmod/chgrp
- **API key missing**: Check environment file exists and is loaded
- **Import errors**: Verify virtual environment is activated

## Emergency Recovery
```bash
# Full system verification
source venv/bin/activate && python quick_3question_benchmark_final.py
```

If this fails, check each component systematically.