# Security Guide for Claude AI

## Security Scanning with Bandit

### Purpose
Bandit is used for **periodic security scans** only, not CI/CD. Run scans when adding new code or reviewing security.

### Running Bandit Scan
```bash
# Install bandit if needed
pip install bandit

# Run security scan
bandit -r . -x venv/,archive/

# Save results for review
bandit -r . -x venv/,archive/ -f json -o security_scan.json
```

### Handling Scan Results

#### 1. Review Findings
```bash
# Human-readable output
bandit -r . -x venv/,archive/ -f txt

# Focus on high/medium severity
bandit -r . -x venv/,archive/ -ll
```

#### 2. Create Whitelist for Accepted Risks
Create `.bandit` configuration file for accepted issues:

```yaml
# .bandit configuration file
skips: ['B101', 'B601']  # Skip specific test IDs
exclude_dirs: ['venv', 'archive', 'tests']
```

#### 3. Common Acceptable Risks in This Project
- **B608**: SQL injection (acceptable in controlled database queries)
- **B101**: Assert statements (acceptable in test files)
- **B603**: Subprocess without shell (acceptable for database operations)

### Security Best Practices

#### Environment Variables
```python
# ALWAYS load from file, never hardcode
from dotenv import load_dotenv
import os

load_dotenv('/home/envs/openai.env')
api_key = os.getenv('OPENAI_API_KEY')  # ✅ Good

# NEVER do this:
api_key = "sk-1234567890abcdef"  # ❌ Bad - hardcoded secret
```

#### Database Queries
```python
# Use parameterized queries when possible
query = "SELECT * FROM WOHNUNG WHERE ONR = ?"
params = (object_number,)

# For dynamic SQL (acceptable in this context):
# Document the reason and ensure input validation
```

#### File Permissions
```bash
# Secure database file
chmod 660 WINCASA2022.FDB  # Read/write for owner and group only

# Secure environment file
chmod 600 /home/envs/openai.env  # Read/write for owner only
```

### Periodic Security Review

#### Monthly Tasks
1. Run bandit scan
2. Review new findings
3. Update whitelist if needed
4. Check environment file permissions
5. Verify database access controls

#### After Code Changes
1. Run targeted bandit scan on changed files
2. Review any new security warnings
3. Update documentation if new risks accepted

### Sample .bandit Configuration

```ini
[bandit]
# Exclude directories
exclude_dirs = venv,archive,tests,docs

# Skip specific tests that are acceptable in this context
skips = B101,B601,B608

# Only report high and medium confidence issues
confidence = MEDIUM

# Custom message for accepted risks
msg_template = {abspath}:{line}: [{test_id}] {msg}
```

### Security Checklist for Claude

When implementing new features:

✅ **Environment Variables**
- Load from `/home/envs/openai.env`
- Never hardcode API keys
- Use `os.getenv()` with defaults

✅ **Database Security**
- Maintain file permissions (660)
- Use service account (firebird group)
- Log access appropriately

✅ **Input Validation**
- Validate user queries
- Sanitize database inputs where possible
- Document acceptable dynamic SQL usage

✅ **Error Handling**
- Don't expose sensitive information in errors
- Log security events appropriately
- Provide generic error messages to users

### No CI/CD Integration

This project **does not use GitHub Actions** or automated CI/CD pipelines. Bandit is run manually for periodic security reviews only.

Security scanning workflow:
1. **Manual execution** when needed
2. **Review findings** with development team
3. **Accept or fix** identified issues
4. **Update whitelist** for accepted risks
5. **Document decisions** in security review notes