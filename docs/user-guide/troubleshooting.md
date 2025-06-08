# Troubleshooting Guide for Claude AI

## Primary Diagnostic

### Always Start Here
```bash
# Run the main verification script
python quick_3question_benchmark_final.py
```

If this shows **less than 9/9 modes working**, follow the steps below.

## Common Issues and Solutions

### 1. Database Connection Failed

**Symptoms**: Error messages about Firebird connection, permission denied

**Solutions**:
```bash
# Check Firebird service
sudo systemctl status firebird

# Start if stopped
sudo systemctl start firebird

# Fix file permissions
sudo chgrp firebird WINCASA2022.FDB
sudo chmod 660 WINCASA2022.FDB

# Verify permissions
ls -la WINCASA2022.FDB
# Should show: -rw-rw---- firebird firebird
```

### 2. Environment Variables Missing

**Symptoms**: API key errors, authentication failures

**Solutions**:
```bash
# Check if environment file exists
ls -la /home/envs/openai.env

# Verify content (don't show keys)
echo "OpenAI key exists:" $(grep -c "OPENAI_API_KEY" /home/envs/openai.env)
echo "OpenRouter key exists:" $(grep -c "OPENROUTER_API_KEY" /home/envs/openai.env)

# Test loading in Python
python -c "
from dotenv import load_dotenv
import os
load_dotenv('/home/envs/openai.env')
print('OpenAI:', 'Found' if os.getenv('OPENAI_API_KEY') else 'Missing')
print('OpenRouter:', 'Found' if os.getenv('OPENROUTER_API_KEY') else 'Missing')
"
```

### 3. Import Errors

**Symptoms**: ModuleNotFoundError, import failures

**Solutions**:
```bash
# Verify virtual environment is active
which python
# Should show: /home/projects/langchain_project/venv/bin/python

# Activate if needed
source venv/bin/activate

# Check required packages
pip list | grep -E "(langchain|openai|sqlalchemy|fdb)"
```

### 4. Individual Mode Failures

**Symptoms**: Some modes work, others don't

**Diagnostic**:
```python
# Test individual components
python -c "
# Test document-based modes
from langchain_core.documents import Document
print('Document import: OK')

# Test database modes  
import sqlalchemy
print('SQLAlchemy import: OK')

# Test LLM
from gemini_llm import get_gemini_llm
llm = get_gemini_llm()
print('LLM setup: OK')
"
```

### 5. Performance Issues

**Symptoms**: Modes work but very slow responses

**Check**:
```bash
# Monitor system resources
top

# Check database locks
sudo systemctl status firebird

# Test with single query
python -c "
from quick_3question_benchmark_final import test_enhanced_mode
import time
start = time.time()
result = test_enhanced_mode()
print(f'Enhanced mode test took: {time.time() - start:.1f}s')
"
```

## Systematic Debugging

### Step-by-Step Diagnosis

1. **Environment Check**:
   ```bash
   source venv/bin/activate
   echo "Virtual env: $(which python)"
   ```

2. **Database Check**:
   ```bash
   sudo systemctl status firebird
   ls -la WINCASA2022.FDB
   ```

3. **API Keys Check**:
   ```bash
   python -c "from dotenv import load_dotenv; import os; load_dotenv('/home/envs/openai.env'); print('Keys loaded:', bool(os.getenv('OPENAI_API_KEY')))"
   ```

4. **Dependencies Check**:
   ```bash
   pip list | grep -E "(langchain|openai|fdb|sqlalchemy)"
   ```

5. **Individual Mode Test**:
   ```bash
   python test_9_mode_status.py
   ```

## Recovery Procedures

### Full System Reset
```bash
# 1. Reset database permissions
sudo chgrp firebird WINCASA2022.FDB
sudo chmod 660 WINCASA2022.FDB

# 2. Restart Firebird
sudo systemctl restart firebird

# 3. Verify environment
source venv/bin/activate

# 4. Test system
python quick_3question_benchmark_final.py
```

### Partial Recovery (Some Modes Working)
```bash
# Focus on failed modes only
python test_9_mode_status.py | grep "FAILED"

# Check specific components for failed modes
# Document-based: Check OpenAI key
# Database-based: Check Firebird connection  
# Classifier-based: Check model files
```

## Emergency Contacts

### When All Else Fails
1. **Check Recent Changes**: What was modified last?
2. **Revert Changes**: Go back to last working state
3. **Clean Restart**: Reboot system and try again
4. **Fresh Environment**: Create new virtual environment

### Success Criteria
✅ All 9/9 modes operational
✅ Benchmark completes without errors  
✅ No timeout or connection issues
✅ Results are reasonable and relevant