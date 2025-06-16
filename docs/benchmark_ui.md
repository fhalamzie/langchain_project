# WINCASA Benchmark UI

## Overview

The WINCASA Benchmark UI is a dedicated tool for comparing the performance and results of all 5 WINCASA modes with different LLM models.

## Features

- **Side-by-side comparison** of all 5 modes:
  - JSON Standard (detailed)
  - JSON Vanilla (minimal)
  - SQL Standard (detailed)
  - SQL Vanilla (minimal)
  - Unified Engine (intelligent, no LLM)

- **LLM Model Selection**:
  - GPT-4o Mini (most cost-effective: $0.15/$0.60 per 1M tokens)
  - GPT-4o (premium multimodal: $2.50/$10.00 per 1M tokens)
  - O1 Mini (fast reasoning: $3.00/$12.00 per 1M tokens)
  - O1 (advanced reasoning: $15.00/$60.00 per 1M tokens)
  - GPT-4 Turbo (legacy: $10.00/$30.00 per 1M tokens)

- **Comprehensive Metrics**:
  - Response time for each mode
  - Cost estimation based on token usage
  - Success/failure status
  - Answer length and preview
  - Full answer display in tabs

- **Export Options**:
  - CSV export of benchmark results
  - JSON export with full details

## Running the Benchmark UI

```bash
# Using the provided script
./tools/scripts/run_benchmark.sh

# Or directly with streamlit
streamlit run src/wincasa/core/benchmark_ui.py --server.port 8668
```

The UI will be available at: http://localhost:8668

## Usage

1. **Select LLM Model**: Choose from the sidebar which model to use for LLM-based modes
2. **Enter Query**: Type your query or select from examples
3. **Run Benchmark**: Click the "Run Benchmark" button
4. **View Results**: See comparison table, full answers, performance metrics, and cost analysis
5. **Export**: Download results as CSV or JSON

## Example Queries

- **Simple Lookup**: "Zeige alle Eigentümer"
- **Filtered Search**: "Liste alle Mieter in Berlin"
- **Complex Analysis**: "Analysiere Mieteinnahmen 2024 nach Objekten mit Leerstandsquote"
- **Aggregation**: "Summe aller Kaltmieten gruppiert nach Eigentümer"

## Notes

- The Unified Engine mode does not use LLM and runs independently
- All LLM modes use the selected model from the sidebar
- Cost estimates are based on token usage and current OpenAI pricing
- Results are displayed in real-time as each mode completes