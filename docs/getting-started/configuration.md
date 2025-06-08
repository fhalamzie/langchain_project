# Configuration Guide for Claude AI

## Environment Configuration

### Required Environment File
**Location**: `/home/envs/openai.env`

```bash
# OpenAI API for document-based retrievers
OPENAI_API_KEY=your_openai_api_key_here

# OpenRouter API for Gemini LLM via OpenRouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### Loading Environment in Code
```python
# ALWAYS use this pattern
from dotenv import load_dotenv
import os

load_dotenv('/home/envs/openai.env')
openai_api_key = os.getenv('OPENAI_API_KEY')
```

## Database Configuration

### Firebird Setup
```bash
# Check if Firebird is running
sudo systemctl status firebird

# Start if needed
sudo systemctl start firebird

# Enable auto-start
sudo systemctl enable firebird
```

### Database File Permissions
```bash
# CRITICAL: Set correct permissions
sudo chgrp firebird WINCASA2022.FDB
sudo chmod 660 WINCASA2022.FDB

# Verify permissions
ls -la WINCASA2022.FDB
# Should show: -rw-rw---- firebird firebird
```

### Connection String Format
```python
# EXACT format required (note double slash)
db_connection = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"

# Components:
# - firebird+fdb: Driver
# - sysdba:masterkey: Username:password
# - localhost:3050: Host:port
# - //absolute/path: Double slash for absolute paths
```

## LLM Configuration

### Current Setup (Gemini via OpenRouter)
```python
# Standard LLM initialization
from gemini_llm import get_gemini_llm
llm = get_gemini_llm()

# Configuration details:
# - Model: google/gemini-pro
# - API: OpenRouter (https://openrouter.ai/api/v1/chat/completions)
# - Key: OPENROUTER_API_KEY from environment
```

## Mock Documents Configuration

### Standard Mock Documents Structure
```python
from langchain_core.documents import Document

def create_mock_documents():
    return [
        Document(
            page_content="""table_name: WOHNUNG
description: Apartment/housing units database
columns:
  - WHG_NR: Apartment number
  - ONR: Object number
  - QMWFL: Living space in square meters
  - ZIMMER: Number of rooms
sample_data:
  - Total apartments: 1250 units
  - Average rent: €850/month""",
            metadata={"table_name": "WOHNUNG", "query_type": "property_count", "source": "WOHNUNG.yaml"}
        ),
        Document(
            page_content="""table_name: BEWOHNER
description: Residents and tenants database
columns:
  - BNAME: Last name
  - BVNAME: First name
  - BSTR: Street address
  - BPLZORT: Postal code and city
  - ONR: Object number
sample_data:
  - "Petra Nabakowski" lives at "Marienstr. 26, 45307 Essen" """,
            metadata={"table_name": "BEWOHNER", "query_type": "address_lookup", "source": "BEWOHNER.yaml"}
        ),
        Document(
            page_content="""table_name: EIGENTUEMER
description: Property owners database
columns:
  - NAME: Owner name
  - VNAME: First name
  - ORT: City
  - EMAIL: Contact email
sample_data:
  - "Immobilien GmbH" from "Köln"
  - "Weber, Klaus" from "Düsseldorf" """,
            metadata={"table_name": "EIGENTUEMER", "query_type": "owner_lookup", "source": "EIGENTUEMER.yaml"}
        )
    ]
```

## Configuration Verification

### Test All Configurations
```bash
# Verify complete setup
python quick_3question_benchmark_final.py

# Should output:
# 🎯 Working Modes: 9/9
# ✅ Functional: [all 9 modes listed]
# 🎉 EXCELLENT! System ready for production!
```

### Individual Component Tests
```python
# Test environment loading
from dotenv import load_dotenv
import os
load_dotenv('/home/envs/openai.env')
print("OpenAI Key:", os.getenv('OPENAI_API_KEY')[:10] + "..." if os.getenv('OPENAI_API_KEY') else "Missing")

# Test database connection
import sqlalchemy
engine = sqlalchemy.create_engine("firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB")
print("Database:", "Connected" if engine else "Failed")

# Test LLM
from gemini_llm import get_gemini_llm
llm = get_gemini_llm()
print("LLM:", "Configured" if llm else "Failed")
```

## Troubleshooting Configuration

### Common Issues
1. **Environment not loaded**: Check file path and permissions
2. **Database permission denied**: Fix file permissions with chmod/chgrp
3. **API key invalid**: Verify keys in environment file
4. **Connection string wrong**: Double-check double slash format

### Configuration Recovery
If configuration is broken, reset with:
```bash
# Reset database permissions
sudo chgrp firebird WINCASA2022.FDB
sudo chmod 660 WINCASA2022.FDB

# Restart Firebird
sudo systemctl restart firebird

# Test configuration
python quick_3question_benchmark_final.py
```