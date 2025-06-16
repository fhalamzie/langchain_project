#!/usr/bin/env python3
"""
WINCASA Benchmark API - Minimal CGI endpoint for HTMX
Executes benchmark queries and returns HTML responses
"""

import json
import os
import sys
import time
from datetime import datetime
import cgi
import cgitb

# Enable CGI error reporting
cgitb.enable()

# Add project to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

# Import WINCASA modules
from wincasa.core.llm_handler import WincasaLLMHandler
from wincasa.core.wincasa_query_engine import WincasaQueryEngine

# Global handlers (initialize once)
llm_handler = None
query_engine = None

def init_handlers():
    """Initialize handlers if not already done"""
    global llm_handler, query_engine
    
    if not llm_handler:
        llm_handler = WincasaLLMHandler()
    if not query_engine:
        query_engine = WincasaQueryEngine()

def execute_mode(query, mode, model):
    """Execute query in a single mode"""
    start_time = time.time()
    
    try:
        if mode == 'unified':
            # Unified engine doesn't use LLM model
            result = query_engine.process_query(query)
            return {
                'success': True,
                'answer': result.answer,
                'time': round(time.time() - start_time, 2),
                'confidence': result.confidence,
                'cost': result.cost_estimate,
                'processing_mode': result.processing_mode
            }
        else:
            # LLM-based modes
            os.environ['OPENAI_MODEL'] = model
            result = llm_handler.query_llm(query, mode)
            
            return {
                'success': result.get('success', True),
                'answer': result.get('answer', 'No answer'),
                'time': round(time.time() - start_time, 2),
                'cost': 0.001,  # Simple estimation
                'source': result.get('source', mode)
            }
    except Exception as e:
        return {
            'success': False,
            'answer': f"Error: {str(e)}",
            'time': round(time.time() - start_time, 2),
            'cost': 0,
            'error': str(e)
        }

def format_results_html(query, model, results):
    """Format results as HTML for HTMX"""
    html = f"""
    <div class="results-header">
        <h2>📊 Benchmark Results</h2>
        <div class="query-info">
            <strong>Query:</strong> {query}<br>
            <strong>Model:</strong> {model}
        </div>
    </div>
    
    <table class="comparison-table">
        <thead>
            <tr>
                <th>Mode</th>
                <th>Status</th>
                <th>Time (s)</th>
                <th>Cost ($)</th>
                <th>Answer Length</th>
            </tr>
        </thead>
        <tbody>
    """
    
    modes = {
        'json_standard': '📊 JSON Standard',
        'json_vanilla': '📋 JSON Vanilla',
        'sql_standard': '🔍 SQL Standard',
        'sql_vanilla': '⚡ SQL Vanilla',
        'unified': '🚀 Unified Engine'
    }
    
    for mode, result in results.items():
        status = '<span class="status-success">✅</span>' if result['success'] else '<span class="status-error">❌</span>'
        html += f"""
            <tr>
                <td>{modes[mode]}</td>
                <td>{status}</td>
                <td>{result['time']}</td>
                <td>{result.get('cost', 0):.4f}</td>
                <td>{len(result['answer'])}</td>
            </tr>
        """
    
    html += """
        </tbody>
    </table>
    
    <div class="mode-results">
        <div class="tabs">
    """
    
    # Add tabs
    for i, (mode, mode_name) in enumerate(modes.items()):
        active = 'active' if i == 0 else ''
        html += f'<button class="tab {active}" data-tab="{mode}" onclick="switchTab(\'{mode}\')">{mode_name}</button>'
    
    html += '</div>'
    
    # Add tab contents
    for i, (mode, result) in enumerate(results.items()):
        active = 'active' if i == 0 else ''
        html += f"""
        <div id="tab-{mode}" class="tab-content {active}">
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Response Time</div>
                    <div class="metric-value">{result['time']}s</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Cost</div>
                    <div class="metric-value">${result.get('cost', 0):.4f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Status</div>
                    <div class="metric-value">{'✅' if result['success'] else '❌'}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Length</div>
                    <div class="metric-value">{len(result['answer'])}</div>
                </div>
            </div>
            
            <div class="answer-box">
                <h3>Answer:</h3>
                <p>{result['answer']}</p>
            </div>
        </div>
        """
    
    html += """
    </div>
    
    <div class="export-buttons">
        <button class="btn btn-export" onclick="exportCSV()">📥 Export CSV</button>
        <button class="btn btn-export" onclick="exportJSON()">📥 Export JSON</button>
    </div>
    
    <script>
        // Store results for export
        window.benchmarkResults = """ + json.dumps({
            'query': query,
            'model': model,
            'timestamp': datetime.now().isoformat(),
            'results': results
        }) + """;
        
        function exportCSV() {
            // Simple CSV export
            let csv = 'Mode,Status,Time,Cost,Answer\\n';
            const modes = ['json_standard', 'json_vanilla', 'sql_standard', 'sql_vanilla', 'unified'];
            
            modes.forEach(mode => {
                const r = window.benchmarkResults.results[mode];
                csv += `${mode},${r.success ? 'Success' : 'Failed'},${r.time},${r.cost || 0},"${r.answer.replace(/"/g, '""')}"\\n`;
            });
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'benchmark_results.csv';
            a.click();
        }
        
        function exportJSON() {
            const blob = new Blob([JSON.stringify(window.benchmarkResults, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'benchmark_results.json';
            a.click();
        }
    </script>
    """
    
    return html

def main():
    """Main CGI handler"""
    print("Content-Type: text/html\n")
    
    # Parse form data
    form = cgi.FieldStorage()
    query = form.getvalue('query', '')
    model = form.getvalue('model', 'gpt-4o-mini')
    
    if not query:
        print('<div class="error">Please enter a query</div>')
        return
    
    try:
        # Initialize handlers
        init_handlers()
        
        # Execute benchmark
        results = {}
        modes = ['json_standard', 'json_vanilla', 'sql_standard', 'sql_vanilla', 'unified']
        
        for mode in modes:
            results[mode] = execute_mode(query, mode, model)
            time.sleep(0.1)  # Small delay to avoid conflicts
        
        # Return formatted HTML
        print(format_results_html(query, model, results))
        
    except Exception as e:
        print(f'<div class="error">Error: {str(e)}</div>')

if __name__ == '__main__':
    main()