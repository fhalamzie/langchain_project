#!/usr/bin/env python3
"""
Query Intent Recognizer for WINCASA
Analyzes natural language queries to determine intent and extract entities
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    """Query intent types"""
    TENANT_SEARCH = "tenant_search"          # Find tenants by address/name
    OWNER_SEARCH = "owner_search"            # Find owners by address/name
    CONTACT_LOOKUP = "contact_lookup"        # Find phone/email
    RENT_INQUIRY = "rent_inquiry"            # Check rent amount
    VACANCY_STATUS = "vacancy_status"        # Check vacant units
    PAYMENT_STATUS = "payment_status"        # Check open items/payments
    PROPERTY_INFO = "property_info"          # Property details
    FINANCIAL_REPORT = "financial_report"    # Financial summaries
    MEETING_INFO = "meeting_info"            # WEG meetings
    MAINTENANCE_INFO = "maintenance_info"    # Maintenance/repairs
    GENERAL_QUERY = "general_query"          # Unclear intent

@dataclass
class QueryAnalysis:
    """Analysis result for a query"""
    intent: QueryIntent
    entities: Dict[str, Any]
    confidence: float
    keywords: List[str]
    normalized_query: str

class QueryIntentRecognizer:
    """Recognizes intent and entities from natural language queries"""
    
    def __init__(self):
        # Intent patterns
        self.intent_patterns = {
            QueryIntent.TENANT_SEARCH: [
                r'wer wohnt',
                r'mieter.*(?:in|von|bei)',
                r'bewohner',
                r'wohnt.*jemand',
                r'aktuelle.*mieter',
                r'wer.*ist.*mieter'
            ],
            QueryIntent.OWNER_SEARCH: [
                r'eigentümer',
                r'eigentuemer',
                r'besitzer',
                r'wem gehört',
                r'wem gehoert'
            ],
            QueryIntent.CONTACT_LOOKUP: [
                r'tel(?:efon)?(?:nummer)?',
                r'nummer.*von',
                r'kontakt',
                r'email',
                r'handy',
                r'erreich(?:bar|en)',
                r'anruf'
            ],
            QueryIntent.RENT_INQUIRY: [
                r'miete',
                r'was zahlt',
                r'monatlich',
                r'kaltmiete',
                r'warmmiete',
                r'nebenkosten'
            ],
            QueryIntent.VACANCY_STATUS: [
                r'frei(?:e)?.*(?:wohnung|whg)',
                r'leer(?:stand)?',
                r'verfügbar',
                r'bezugsfrei',
                r'vermieten'
            ],
            QueryIntent.PAYMENT_STATUS: [
                r'offen(?:e)?.*(?:miete|zahlung|posten)',
                r'zahlt.*nicht',
                r'mahnung',
                r'schuld',
                r'rückstand',
                r'ausstehend'
            ],
            QueryIntent.PROPERTY_INFO: [
                r'objekt',
                r'gebäude',
                r'liegenschaft',
                r'wie.*viele.*wohnung',
                r'anzahl.*einheit',
                r'qm|quadratmeter'
            ],
            QueryIntent.MEETING_INFO: [
                r'versammlung',
                r'etv',
                r'weg.*versammlung',
                r'nächste.*termin',
                r'beschluss',
                r'protokoll'
            ]
        }
        
        # Entity patterns
        self.entity_patterns = {
            'street': r'(?:straße|strasse|str\.?|weg|platz|allee|gasse)\s*\d*',
            'name': r'(?:herr|frau|familie|fam\.?)\s+\w+',
            'number': r'\d+',
            'postal_code': r'\b\d{5}\b',
            'city': r'(?:essen|bochum|düsseldorf|köln|dortmund)'
        }
        
        # Common typos and variations
        self.typo_corrections = {
            'marienstr': 'marienstraße',
            'kämpenstr': 'kämpenstraße',
            'kämpennstraße': 'kämpenstraße',
            'borowsky': 'borowski',
            'nabakowsky': 'nabakowski',
            'halamzei': 'halamzie',
            'whg': 'wohnung',
            'tel': 'telefon',
            'nr': 'nummer'
        }
    
    def analyze(self, query: str) -> QueryAnalysis:
        """Analyze query to determine intent and extract entities"""
        # Normalize query
        normalized = self._normalize_query(query)
        
        # Extract keywords
        keywords = self._extract_keywords(normalized)
        
        # Determine intent
        intent, confidence = self._determine_intent(normalized, keywords)
        
        # Extract entities
        entities = self._extract_entities(query, normalized, intent)
        
        return QueryAnalysis(
            intent=intent,
            entities=entities,
            confidence=confidence,
            keywords=keywords,
            normalized_query=normalized
        )
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query: lowercase, fix typos, standardize"""
        normalized = query.lower().strip()
        
        # Remove excessive punctuation
        normalized = re.sub(r'[?!]{2,}', '?', normalized)
        normalized = re.sub(r'\.{2,}', '', normalized)
        
        # Apply typo corrections
        for typo, correction in self.typo_corrections.items():
            normalized = normalized.replace(typo, correction)
        
        # Standardize spaces
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _extract_keywords(self, normalized_query: str) -> List[str]:
        """Extract important keywords from query"""
        # Remove common words
        stop_words = {'der', 'die', 'das', 'in', 'von', 'mit', 'bei', 'zu', 
                     'ich', 'bin', 'ist', 'sind', 'wie', 'was', 'wer', 'wo'}
        
        words = normalized_query.split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    def _determine_intent(self, normalized_query: str, keywords: List[str]) -> Tuple[QueryIntent, float]:
        """Determine query intent with confidence score"""
        intent_scores = {}
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, normalized_query, re.IGNORECASE):
                    score += 1
            
            if score > 0:
                intent_scores[intent] = score
        
        # If no clear intent, use keyword matching
        if not intent_scores:
            for keyword in keywords:
                for intent, patterns in self.intent_patterns.items():
                    for pattern in patterns:
                        if keyword in pattern or pattern in keyword:
                            intent_scores[intent] = intent_scores.get(intent, 0) + 0.5
        
        # Get best match
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            max_score = intent_scores[best_intent]
            confidence = min(max_score / 3, 1.0)  # Normalize to 0-1
            return best_intent, confidence
        
        return QueryIntent.GENERAL_QUERY, 0.0
    
    def _extract_entities(self, original_query: str, normalized_query: str, intent: QueryIntent) -> Dict[str, Any]:
        """Extract entities based on intent"""
        entities = {}
        
        # Extract street addresses
        street_match = re.search(r'(\w+(?:straße|strasse|str\.?|weg|platz))\s*(\d+\w*)?', normalized_query, re.IGNORECASE)
        if street_match:
            street_name = street_match.group(1)
            # Capitalize properly
            street_name = street_name[0].upper() + street_name[1:]
            if 'straße' not in street_name and 'strasse' not in street_name:
                street_name += 'straße'
            
            entities['street'] = street_name
            if street_match.group(2):
                entities['house_number'] = street_match.group(2)
        
        # Extract names (for contact lookup)
        if intent == QueryIntent.CONTACT_LOOKUP:
            # Look for personal names
            name_patterns = [
                r'(?:herr|frau)\s+(\w+)',
                r'(?:von|für)\s+(\w+)',
                r'(\w+)\s+(?:telefon|tel|nummer|kontakt|email)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, normalized_query, re.IGNORECASE)
                if match:
                    name = match.group(1)
                    # Capitalize
                    entities['name'] = name[0].upper() + name[1:]
                    break
            
            # Also check keywords that might be names
            if 'name' not in entities:
                potential_names = ['borowski', 'nabakowski', 'halamzie', 'yildirim', 
                                 'blessing', 'blesing', 'hashimi', 'acar']
                for keyword in self._extract_keywords(normalized_query):
                    for name in potential_names:
                        if keyword.startswith(name[:4]):  # Fuzzy match
                            entities['name'] = name.capitalize()
                            break
        
        # Extract postal codes
        postal_match = re.search(r'\b(\d{5})\b', normalized_query)
        if postal_match:
            entities['postal_code'] = postal_match.group(1)
        
        # Extract city names
        cities = ['essen', 'bochum', 'düsseldorf', 'köln', 'dortmund']
        for city in cities:
            if city in normalized_query:
                entities['city'] = city.capitalize()
                break
        
        return entities
    
    def get_search_parameters(self, analysis: QueryAnalysis) -> Dict[str, Any]:
        """Convert analysis to search parameters"""
        params = {
            'intent': analysis.intent.value,
            'confidence': analysis.confidence
        }
        
        # Add search fields based on intent
        if analysis.intent == QueryIntent.TENANT_SEARCH:
            if 'street' in analysis.entities:
                params['search_address'] = analysis.entities['street']
                if 'house_number' in analysis.entities:
                    params['search_address'] += ' ' + analysis.entities['house_number']
            if 'name' in analysis.entities:
                params['search_name'] = analysis.entities['name']
        
        elif analysis.intent == QueryIntent.CONTACT_LOOKUP:
            if 'name' in analysis.entities:
                params['search_name'] = analysis.entities['name']
        
        elif analysis.intent == QueryIntent.OWNER_SEARCH:
            if 'street' in analysis.entities:
                params['search_address'] = analysis.entities['street']
                if 'house_number' in analysis.entities:
                    params['search_address'] += ' ' + analysis.entities['house_number']
        
        # Add location filters
        if 'postal_code' in analysis.entities:
            params['postal_code'] = analysis.entities['postal_code']
        if 'city' in analysis.entities:
            params['city'] = analysis.entities['city']
        
        return params