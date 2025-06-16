#!/usr/bin/env python3
"""
Simple HTTP server for HTMX benchmark UI
Serves static files and handles API requests
"""

import os
import sys
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import subprocess

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from wincasa.core.llm_handler import WincasaLLMHandler
from wincasa.core.wincasa_query_engine import WincasaQueryEngine
from wincasa.utils.text_to_table_parser import extract_table_from_answer, is_table_data

# Initialize handlers
llm_handler = WincasaLLMHandler()
query_engine = WincasaQueryEngine()

class BenchmarkHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve static files"""
        if self.path == '/' or self.path == '/index.html':
            self.serve_file('benchmark.html', 'text/html')
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle API requests"""
        if self.path == '/api/benchmark':
            self.handle_benchmark()
        else:
            self.send_error(404)
    
    def serve_file(self, filename, content_type):
        """Serve a static file"""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)
    
    def handle_benchmark(self):
        """Handle benchmark API request"""
        # Read POST data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Parse form data
        params = {}
        for param in post_data.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key] = value.replace('+', ' ').replace('%3F', '?')
        
        query = params.get('query', '')
        model = params.get('model', 'gpt-4o-mini')
        
        if not query:
            self.send_error(400, 'Query is required')
            return
        
        # Execute benchmark
        results = self.run_benchmark(query, model)
        
        # Generate HTML response
        html = self.format_results_html(query, model, results)
        
        # Send response
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(html.encode()))
        self.end_headers()
        self.wfile.write(html.encode())
    
    def run_benchmark(self, query, model):
        """Run benchmark across all modes"""
        results = {}
        modes = ['json_standard', 'json_vanilla', 'sql_standard', 'sql_vanilla', 'unified']
        
        for mode in modes:
            results[mode] = self.execute_mode(query, mode, model)
            time.sleep(0.1)  # Avoid conflicts
        
        return results
    
    def execute_mode(self, query, mode, model):
        """Execute query in a single mode"""
        start_time = time.time()
        
        try:
            if mode == 'unified':
                result = query_engine.process_query(query)
                return {
                    'success': True,
                    'answer': result.answer,
                    'time': round(time.time() - start_time, 2),
                    'confidence': result.confidence,
                    'cost': result.cost_estimate
                }
            else:
                os.environ['OPENAI_MODEL'] = model
                result = llm_handler.query_llm(query, mode)
                return {
                    'success': result.get('success', True),
                    'answer': result.get('answer', 'No answer'),
                    'time': round(time.time() - start_time, 2),
                    'cost': 0.001
                }
        except Exception as e:
            return {
                'success': False,
                'answer': f"Error: {str(e)}",
                'time': round(time.time() - start_time, 2),
                'cost': 0
            }
    
    def format_answer_html(self, answer, mode):
        """Format answer with JSON detection and table view"""
        # Try to detect JSON
        is_json = False
        json_data = None
        table_html = None
        remaining_text = None
        
        if isinstance(answer, str) and (answer.strip().startswith('{') or answer.strip().startswith('[')):
            try:
                json_data = json.loads(answer)
                is_json = True
            except:
                pass
        
        # If not JSON, try to extract table from text
        if not is_json and isinstance(answer, str) and is_table_data(answer):
            import pandas as pd
            table_df, remaining_text = extract_table_from_answer(answer)
            if table_df is not None and not table_df.empty:
                table_html = self._dataframe_to_html(table_df)
        
        if is_json and json_data:
            # Generate table HTML if possible
            table_html = self._json_to_table_html(json_data)
            
            # Create toggleable Table/JSON/Text view
            return f"""
            <div class="answer-format-toggle">
                <label>
                    <input type="radio" name="format_{mode}" value="table" {"checked" if table_html else ""} onclick="showFormat_{mode}('table')"> Table
                </label>
                <label>
                    <input type="radio" name="format_{mode}" value="json" {"checked" if not table_html else ""} onclick="showFormat_{mode}('json')"> JSON
                </label>
                <label>
                    <input type="radio" name="format_{mode}" value="text" onclick="showFormat_{mode}('text')"> Text
                </label>
            </div>
            <div id="table_{mode}" class="table-view" style="{'display:block;' if table_html else 'display:none;'}">
                {table_html if table_html else '<p>Data not suitable for table display</p>'}
            </div>
            <div id="json_{mode}" class="json-view" style="{'display:none;' if table_html else 'display:block;'}">
                <pre>{json.dumps(json_data, indent=2, ensure_ascii=False)}</pre>
            </div>
            <div id="text_{mode}" class="text-view" style="display:none;">
                <p>{answer}</p>
            </div>
            <script>
                function showFormat_{mode}(format) {{
                    document.getElementById('table_{mode}').style.display = format === 'table' ? 'block' : 'none';
                    document.getElementById('json_{mode}').style.display = format === 'json' ? 'block' : 'none';
                    document.getElementById('text_{mode}').style.display = format === 'text' ? 'block' : 'none';
                }}
            </script>
            """
        elif table_html:
            # Text with extracted table
            return f"""
            <div class="answer-format-toggle">
                <label>
                    <input type="radio" name="format_{mode}" value="table" checked onclick="showFormat_{mode}('table')"> Table
                </label>
                <label>
                    <input type="radio" name="format_{mode}" value="text" onclick="showFormat_{mode}('text')"> Text
                </label>
            </div>
            <div id="table_{mode}" class="table-view">
                {remaining_text if remaining_text else ''}
                {table_html}
            </div>
            <div id="text_{mode}" class="text-view" style="display:none;">
                <p>{answer}</p>
            </div>
            <script>
                function showFormat_{mode}(format) {{
                    document.getElementById('table_{mode}').style.display = format === 'table' ? 'block' : 'none';
                    document.getElementById('text_{mode}').style.display = format === 'text' ? 'block' : 'none';
                }}
            </script>
            """
        else:
            # Regular text
            return f"<p>{answer}</p>"
    
    def _json_to_table_html(self, json_data):
        """Convert JSON data to HTML table"""
        try:
            if isinstance(json_data, list) and len(json_data) > 0:
                # List of records - create table
                if all(isinstance(item, dict) for item in json_data):
                    # Get all unique keys
                    all_keys = set()
                    for item in json_data:
                        all_keys.update(item.keys())
                    all_keys = sorted(all_keys)
                    
                    # Build table
                    html = '<table class="json-table">'
                    # Header
                    html += '<thead><tr>'
                    for key in all_keys:
                        html += f'<th>{key}</th>'
                    html += '</tr></thead>'
                    
                    # Body
                    html += '<tbody>'
                    for item in json_data[:100]:  # Limit to 100 rows
                        html += '<tr>'
                        for key in all_keys:
                            value = item.get(key, '')
                            html += f'<td>{value}</td>'
                        html += '</tr>'
                    html += '</tbody>'
                    html += '</table>'
                    
                    if len(json_data) > 100:
                        html += f'<p><em>Showing first 100 of {len(json_data)} records</em></p>'
                    
                    return html
                    
            elif isinstance(json_data, dict):
                # Single record - create simple table
                if all(isinstance(v, (str, int, float, bool, type(None))) for v in json_data.values()):
                    html = '<table class="json-table">'
                    html += '<thead><tr>'
                    for key in json_data.keys():
                        html += f'<th>{key}</th>'
                    html += '</tr></thead>'
                    html += '<tbody><tr>'
                    for value in json_data.values():
                        html += f'<td>{value}</td>'
                    html += '</tr></tbody>'
                    html += '</table>'
                    return html
                    
        except Exception as e:
            print(f"Error converting JSON to table: {e}")
        
        return None
    
    def _dataframe_to_html(self, df):
        """Convert pandas DataFrame to HTML table"""
        try:
            html = '<table class="json-table">'
            # Header
            html += '<thead><tr>'
            for col in df.columns:
                html += f'<th>{col}</th>'
            html += '</tr></thead>'
            
            # Body
            html += '<tbody>'
            for _, row in df.iterrows():
                html += '<tr>'
                for value in row.values:
                    html += f'<td>{value}</td>'
                html += '</tr>'
            html += '</tbody>'
            html += '</table>'
            
            return html
        except Exception as e:
            print(f"Error converting DataFrame to HTML: {e}")
            return None
    
    def format_results_html(self, query, model, results):
        """Format results as HTML"""
        modes = {
            'json_standard': '📊 JSON Standard',
            'json_vanilla': '📋 JSON Vanilla',
            'sql_standard': '🔍 SQL Standard',
            'sql_vanilla': '⚡ SQL Vanilla',
            'unified': '🚀 Unified Engine'
        }
        
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
        
        for mode, result in results.items():
            status = '✅' if result['success'] else '❌'
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
                </div>
                
                <div class="answer-box">
                    <h3>Answer:</h3>
                    {self.format_answer_html(result['answer'], mode)}
                </div>
            </div>
            """
        
        html += '</div>'
        
        return html

def main():
    """Run the server"""
    port = 8669
    server = HTTPServer(('0.0.0.0', port), BenchmarkHandler)
    print(f"🔬 HTMX Benchmark Server running on http://0.0.0.0:{port}")
    print(f"📍 Access at: http://localhost:{port} or http://192.168.178.4:{port}")
    server.serve_forever()

if __name__ == '__main__':
    main()