---
name: Performance Issue
about: Report performance problems in the WINCASA system
title: '[PERFORMANCE] '
labels: ['performance']
assignees: ''
---

## ⚡ Performance Issue Description

A clear and concise description of the performance problem.

## 📊 Current Performance Metrics

**Query Performance:**
- Query execution time: [e.g., 45 seconds]
- Expected execution time: [e.g., under 25 seconds]
- Success rate: [e.g., 60%]

**Retrieval Performance:**
- Retrieval mode used: [Enhanced / FAISS / None]
- Documents retrieved: [e.g., 15]
- Retrieval time: [e.g., 5 seconds]
- Relevance scores: [e.g., average 0.7]

**Phoenix Monitoring Data:**
- Total tokens used: [e.g., 2000]
- Cost per query: [e.g., $0.05]
- LLM response time: [e.g., 3 seconds]

## 🎯 Performance Goals

**Desired Performance:**
- Target query time: [e.g., under 20 seconds]
- Target success rate: [e.g., 85%+]
- Target cost per query: [e.g., under $0.02]

## 🔄 Reproduction Steps

1. Configure system with: [specific settings]
2. Execute query: "[specific query]"
3. Measure performance using: [Phoenix dashboard / logs / manual timing]
4. Observe: [specific performance issue]

## 📈 Performance Profile

**Query Type:**
- [ ] Simple table lookup
- [ ] Complex multi-table joins
- [ ] Aggregation queries
- [ ] Full-text search
- [ ] Other: [specify]

**Query Complexity:**
- [ ] Low (1-2 tables)
- [ ] Medium (3-5 tables)
- [ ] High (6+ tables)

**Data Volume:**
- Database size: [e.g., 500MB]
- Number of relevant tables: [e.g., 5]
- Estimated result size: [e.g., 100 rows]

## 🖥️ System Environment

**Hardware:**
- CPU: [e.g., Intel i7-10700K]
- RAM: [e.g., 16GB]
- Storage: [e.g., SSD]
- Network: [e.g., 1Gbps LAN / WiFi]

**Software:**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.10.5]
- WINCASA version: [e.g., v1.0.0]
- Firebird version: [e.g., 3.0.7]

## ⚙️ Configuration

**WINCASA Settings:**
- Retrieval mode: [Enhanced / FAISS / None]
- Enhanced knowledge: [Enabled / Disabled]
- Document mode: [yaml_only / all / markdown_only]
- Phoenix monitoring: [Enabled / Disabled]

**Database Configuration:**
- Connection type: [Server / Embedded]
- Connection string: [sanitized, no passwords]
- Firebird page size: [e.g., 8192]
- Database cache: [e.g., default]

## 📊 Benchmarking Data

**Phoenix Dashboard Screenshots:**
[Attach Phoenix monitoring screenshots if available]

**Detailed Timings:**
```
[Paste detailed timing logs here]
```

**Memory Usage:**
- Peak memory usage: [e.g., 2.5GB]
- Average memory usage: [e.g., 1.8GB]

**Network Activity:**
- Database queries: [e.g., 5 queries]
- API calls: [e.g., 3 OpenAI calls]
- Data transferred: [e.g., 50KB]

## 🔍 Analysis

**Suspected Bottlenecks:**
- [ ] Database query optimization
- [ ] LLM API response time
- [ ] Document retrieval efficiency
- [ ] Python code performance
- [ ] Network latency
- [ ] Memory management
- [ ] Other: [specify]

**Phoenix Insights:**
[Any insights from Phoenix monitoring dashboard]

## 🎯 Impact

**Business Impact:**
- [ ] No impact (isolated case)
- [ ] Minor impact (occasional delays)
- [ ] Moderate impact (affects daily workflow)
- [ ] Major impact (severely affects productivity)

**User Experience:**
- [ ] Barely noticeable
- [ ] Annoying but usable
- [ ] Significantly impacts usability
- [ ] Makes system unusable

## 🚀 Potential Solutions

**Have you tried any optimizations?**
- [ ] Different retrieval mode
- [ ] Query reformulation
- [ ] Database optimization
- [ ] Configuration changes
- [ ] Other: [describe]

**Results of attempted solutions:**
[Describe what you tried and the results]

## 📋 Additional Context

**Comparison with similar queries:**
[How does this perform compared to similar queries?]

**Historical performance:**
[Has performance degraded over time?]

**Load conditions:**
[Was system under heavy load when issue occurred?]

## ✅ Checklist

- [ ] I have provided Phoenix monitoring data (if available)
- [ ] I have included specific timing measurements
- [ ] I have described the system environment
- [ ] I have attempted basic troubleshooting
- [ ] I have searched for similar performance issues