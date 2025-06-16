#!/usr/bin/env python3
"""
Text to Table Parser
Parses structured text output from WINCASA into table format
"""

import re
import pandas as pd
from typing import List, Dict, Optional, Tuple


def parse_wincasa_text_to_data(text: str) -> Optional[List[Dict]]:
    """
    Parse WINCASA formatted text output into structured data.
    
    Handles formats like:
    1. EIGNR: 455 | EANREDE: Herr | EVNAME: Maxim | ENAME: Janz
    2. KNR: 100100 | ONR: 1 | ENR: 1 | WOHNUNGSBEZEICHNUNG: EG
    """
    
    # Look for numbered list pattern
    lines = text.split('\n')
    data_lines = []
    
    # Find lines that match pattern: "N. KEY: value | KEY: value"
    pattern = re.compile(r'^\d+\.\s+(.+)$')
    
    for line in lines:
        match = pattern.match(line.strip())
        if match:
            data_lines.append(match.group(1))
    
    if not data_lines:
        return None
    
    # Parse each data line
    records = []
    for line in data_lines:
        record = {}
        
        # Split by pipe and parse key-value pairs
        parts = line.split(' | ')
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                record[key.strip()] = value.strip()
        
        if record:
            records.append(record)
    
    return records if records else None


def extract_table_from_answer(answer: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Extract table data from WINCASA answer text.
    Returns (DataFrame, remaining_text) or (None, original_text)
    """
    
    # Try to parse as WINCASA formatted data
    data = parse_wincasa_text_to_data(answer)
    
    if data and len(data) > 0:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Extract non-data parts (headers, summaries)
        lines = answer.split('\n')
        header_lines = []
        data_started = False
        footer_lines = []
        
        for line in lines:
            if re.match(r'^\d+\.\s+', line.strip()):
                data_started = True
            elif not data_started:
                header_lines.append(line)
            elif data_started and not re.match(r'^\d+\.\s+', line.strip()):
                footer_lines.append(line)
        
        # Combine non-data text
        remaining_text = '\n'.join(header_lines + footer_lines).strip()
        
        return df, remaining_text
    
    return None, answer


def is_table_data(text: str) -> bool:
    """Check if text contains parseable table data"""
    # Look for patterns like "1. KEY: value | KEY: value"
    pattern = re.compile(r'^\d+\.\s+\w+:\s*[^|]+\|', re.MULTILINE)
    return bool(pattern.search(text))