# Quick Start Guide for Claude AI

## Immediate Verification

Before making any changes, ALWAYS verify the system is working:

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Run verification test
python quick_3question_benchmark_final.py
```

**Expected Result**: All 9/9 modes should be functional.

## Making Changes

### Safe Change Process
1. **Verify baseline**: Run `quick_3question_benchmark_final.py`
2. **Make minimal changes**: Follow exact patterns from documentation
3. **Test immediately**: Re-run benchmark after each change
4. **If broken**: Revert changes immediately

### Key Files to Never Modify
- `quick_3question_benchmark_final.py` - Main verification script
- `gemini_llm.py` - LLM configuration
- Database connection strings - Format is critical
- Retriever initialization patterns - Tested and working

## Common Tasks

### Testing a Single Mode
```python
# Use this pattern for any retriever testing
from gemini_llm import get_gemini_llm
llm = get_gemini_llm()

# Test any retriever
def test_mode(retriever, query="How many apartments are there?"):
    if hasattr(retriever, 'get_response'):
        return retriever.get_response(query)
    elif hasattr(retriever, 'query'):
        return retriever.query(query)
    elif hasattr(retriever, 'retrieve'):
        result = retriever.retrieve(query)
        # Handle result based on type...
```

### Adding New Functionality
1. Check existing patterns in `/docs/development/implementation-guide.md`
2. Follow initialization patterns from `/docs/technical/retriever-modes.md`
3. Test with standard 3-question benchmark
4. Ensure all 9 modes remain functional

## Emergency Commands

### If System Breaks
```bash
# Check database
sudo systemctl status firebird

# Check environment
echo $OPENAI_API_KEY

# Check permissions
ls -la WINCASA2022.FDB

# Full recovery test
python quick_3question_benchmark_final.py
```

### Recovery Steps
1. Fix database permissions if needed
2. Restart Firebird if locked
3. Check environment variables
4. Run verification test again

## Success Criteria

✅ All 9 modes functional
✅ Benchmark completes without errors
✅ Database accessible
✅ Environment configured