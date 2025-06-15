#!/usr/bin/env python3
"""
WINCASA Phase 2.3 - Hierarchical Intent Router
3-stufiges System: Regex → LLM → Fallback für optimale Intent-Erkennung
"""

import json
import re
import os
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# OpenAI für LLM-Klassifizierung
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

@dataclass
class RouterResult:
    """Ergebnis des Intent Routers"""
    intent_id: str
    confidence: float
    router_level: str  # "regex", "llm", "fallback"
    processing_time_ms: float
    extracted_entities: Dict[str, str]
    template_available: bool
    suggested_mode: str  # "template", "structured_search", "legacy_json"

class HierarchicalIntentRouter:
    """
    3-Level Hierarchical Intent Router für WINCASA
    
    Level 1: Regex/Keyword Matching (ultra-fast, hochpräzise)
    Level 2: LLM-basierte Klassifizierung (intelligent, kontextbewusst)
    Level 3: Fallback to Legacy (immer verfügbar)
    
    Performance-Optimiert:
    - Level 1: <1ms Response Time
    - Level 2: ~500ms Response Time  
    - Level 3: <1ms Response Time
    """
    
    def __init__(self, 
                 api_key_file="/home/envs/openai.env",
                 model_name="gpt-4o-mini",
                 debug_mode=False):
        
        self.model_name = model_name
        self.debug_mode = debug_mode
        
        # Load OpenAI API
        self.client = None
        if OPENAI_AVAILABLE and os.path.exists(api_key_file):
            try:
                with open(api_key_file, 'r') as f:
                    for line in f:
                        if line.startswith('OPENAI_API_KEY='):
                            api_key = line.split('=', 1)[1].strip()
                            self.client = OpenAI(api_key=api_key)
                            break
            except Exception as e:
                if self.debug_mode:
                    print(f"⚠️  OpenAI API Load Error: {e}")
        
        # Initialize routing patterns
        self._setup_regex_patterns()
        self._setup_llm_prompts()
        
        if self.debug_mode:
            print(f"✅ Hierarchical Intent Router initialisiert:")
            print(f"   🔍 {len(self.regex_patterns)} Regex-Patterns (Level 1)")
            print(f"   🤖 LLM verfügbar: {self.client is not None} (Level 2)")
            print(f"   🔄 Fallback immer verfügbar (Level 3)")
    
    def _setup_regex_patterns(self):
        """Setup Level 1: Hochpräzise Regex-Patterns"""
        
        self.regex_patterns = {
            # === MIETER PATTERNS ===
            "mieter_search_location": {
                "patterns": [
                    r"wer\s+wohnt\s+in\s+(?:der\s+)?(.+?)(?:\?|$)",
                    r"(?:zeige|liste)\s+(?:mir\s+)?(?:alle\s+)?mieter\s+in\s+(.+?)(?:\?|$)",
                    r"bewohner\s+(?:von|in|der)\s+(.+?)(?:\?|$)",
                    r"mieter\s+(?:von|in|der)\s+(.+?)(?:\?|$)"
                ],
                "confidence": 0.95,
                "template_available": True,
                "template_id": "mieter_by_location",
                "required_entities": ["location"]
            },
            
            "mieter_contact_lookup": {
                "patterns": [
                    r"kontakt(?:daten)?\s+(?:von|für)\s+(.+?)(?:\?|$)",
                    r"telefon(?:nummer)?\s+(?:von|für)\s+(.+?)(?:\?|$)",
                    r"email(?:\-adresse)?\s+(?:von|für)\s+(.+?)(?:\?|$)",
                    r"adresse\s+(?:von|für)\s+(.+?)(?:\?|$)"
                ],
                "confidence": 0.90,
                "template_available": True,
                "template_id": "mieter_contact",
                "required_entities": ["person_name"]
            },
            
            # === EIGENTÜMER PATTERNS ===
            "owner_search": {
                "patterns": [
                    r"eigentümer\s+(?:von|für)\s+(.+?)(?:\?|$)",
                    r"eigentuemer\s+(?:von|für)\s+(.+?)(?:\?|$)",
                    r"wem\s+gehört\s+(.+?)(?:\?|$)",
                    r"besitzer\s+(?:von|für)\s+(.+?)(?:\?|$)"
                ],
                "confidence": 0.92,
                "template_available": True,
                "template_id": "owner_by_property",
                "required_entities": ["location"]
            },
            
            "portfolio_query": {
                "patterns": [
                    r"(?:wie\s+viele\s+)?(?:objekte|immobilien)\s+(?:hat|besitzt)\s+(.+?)(?:\?|$)",
                    r"portfolio\s+(?:von|für)\s+(.+?)(?:\?|$)",
                    r"besitz\s+(?:von|für)\s+(.+?)(?:\?|$)"
                ],
                "confidence": 0.88,
                "template_available": True,
                "template_id": "owner_portfolio",
                "required_entities": ["person_name"]
            },
            
            # === OBJEKT PATTERNS ===
            "vacancy_status": {
                "patterns": [
                    r"(?:freie|leere)\s+wohnungen?\s+in\s+(.+?)(?:\?|$)",
                    r"leerstand\s+in\s+(.+?)(?:\?|$)",
                    r"(?:welche\s+)?wohnungen?\s+(?:sind\s+)?(?:frei|leer)(?:\s+in\s+(.+?))?(?:\?|$)",
                    r"vermietungsgrad\s+(.+?)(?:\?|$)"
                ],
                "confidence": 0.85,
                "template_available": True,
                "template_id": "vacancy_by_location",
                "required_entities": ["location"]
            },
            
            "property_details": {
                "patterns": [
                    r"(?:wie\s+viele\s+)?(?:wohnungen|einheiten)\s+(?:hat|gibt\s+es\s+in)\s+(.+?)(?:\?|$)",
                    r"details\s+(?:zu|über)\s+(.+?)(?:\?|$)",
                    r"(?:info|informationen)\s+(?:zu|über)\s+(.+?)(?:\?|$)"
                ],
                "confidence": 0.80,
                "template_available": True,
                "template_id": "property_details",
                "required_entities": ["location"]
            },
            
            # === FINANZEN PATTERNS ===
            "account_balance": {
                "patterns": [
                    r"(?:konto)?saldo\s+(?:von|für)\s+(.+?)(?:\?|$)",
                    r"kontostand\s+(?:von|für)\s+(.+?)(?:\?|$)",
                    r"(?:schulden|guthaben)\s+(?:von|für)\s+(.+?)(?:\?|$)"
                ],
                "confidence": 0.88,
                "template_available": True,
                "template_id": "account_balance",
                "required_entities": ["person_name"]
            }
        }
    
    def _setup_llm_prompts(self):
        """Setup Level 2: LLM Classification Prompts"""
        
        self.llm_system_prompt = """Du bist ein WINCASA Immobilienverwaltungs-Experte und Intent-Klassifizierer.

Klassifiziere deutsche Immobilienverwaltungs-Anfragen in diese Intent-Kategorien:

MIETER-INTENTS:
- mieter_search_location: Mietersuche nach Adresse/Ort
- mieter_contact_lookup: Kontaktdaten von Mietern
- mieter_payments: Zahlungen, Saldo, Rückstände von Mietern
- mieter_analysis: Mieter-Analysen (Mietdauer, Email-Status, etc.)

EIGENTÜMER-INTENTS:
- owner_search: Eigentümersuche nach Immobilie
- portfolio_query: Portfolio-Anfragen von Eigentümern
- owner_analysis: Eigentümer-Analysen

OBJEKT-INTENTS:
- vacancy_status: Leerstand, freie Wohnungen
- property_details: Objekt-Details, Wohnungsanzahl
- occupancy_analysis: Vermietungsgrad-Analysen

FINANZEN-INTENTS:
- account_balance: Kontostände, Salden
- payment_analysis: Zahlungsanalysen

COMPLEX/ADMIN-INTENTS:
- complex_report: Berichte, umfassende Analysen
- admin_weg: WEG-Verwaltung, Beiräte, Versammlungen

Antworte NUR mit dem Intent-Namen. Falls unsicher, verwende "complex_report"."""

        self.llm_examples = [
            ("Wer wohnt in der Bergstraße 15?", "mieter_search_location"),
            ("Kontaktdaten von Herrn Müller", "mieter_contact_lookup"),
            ("Portfolio von Familie Schmidt", "portfolio_query"),
            ("Freie Wohnungen in Hamburg", "vacancy_status"),
            ("Kontostand von Weber", "account_balance"),
            ("Mieter ohne Email", "mieter_analysis"),
            ("Bericht über alle Rückstände", "complex_report")
        ]
    
    def route_intent(self, query: str) -> RouterResult:
        """
        Hauptfunktion: Hierarchisches Intent Routing
        
        Level 1: Regex Patterns (ultra-fast)
        Level 2: LLM Classification (intelligent)  
        Level 3: Fallback (always available)
        """
        start_time = time.time()
        
        if self.debug_mode:
            print(f"🔍 Router Query: '{query}'")
        
        # LEVEL 1: Regex Pattern Matching
        level1_result = self._try_regex_routing(query)
        if level1_result and level1_result.confidence >= 0.8:
            processing_time = round((time.time() - start_time) * 1000, 2)
            level1_result.processing_time_ms = processing_time
            if self.debug_mode:
                print(f"   ✅ Level 1 Success: {level1_result.intent_id} ({level1_result.confidence:.1%})")
            return level1_result
        
        # LEVEL 2: LLM Classification
        if self.client:
            level2_result = self._try_llm_routing(query)
            if level2_result and level2_result.confidence >= 0.6:
                processing_time = round((time.time() - start_time) * 1000, 2)
                level2_result.processing_time_ms = processing_time
                if self.debug_mode:
                    print(f"   ✅ Level 2 Success: {level2_result.intent_id} ({level2_result.confidence:.1%})")
                return level2_result
        
        # LEVEL 3: Fallback
        fallback_result = self._fallback_routing(query)
        processing_time = round((time.time() - start_time) * 1000, 2)
        fallback_result.processing_time_ms = processing_time
        
        if self.debug_mode:
            print(f"   🔄 Level 3 Fallback: {fallback_result.intent_id}")
        
        return fallback_result
    
    def _try_regex_routing(self, query: str) -> Optional[RouterResult]:
        """Level 1: Regex Pattern Matching"""
        query_lower = query.lower().strip()
        
        best_match = None
        best_score = 0.0
        
        for intent_id, pattern_config in self.regex_patterns.items():
            for pattern in pattern_config["patterns"]:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    # Extract entities from regex groups
                    entities = {}
                    if pattern_config["required_entities"]:
                        if "location" in pattern_config["required_entities"] and match.groups():
                            entities["location"] = match.group(1).strip()
                        elif "person_name" in pattern_config["required_entities"] and match.groups():
                            entities["person_name"] = match.group(1).strip()
                    
                    score = pattern_config["confidence"]
                    
                    if score > best_score:
                        best_score = score
                        best_match = RouterResult(
                            intent_id=intent_id,
                            confidence=score,
                            router_level="regex",
                            processing_time_ms=0.0,  # Set later
                            extracted_entities=entities,
                            template_available=pattern_config["template_available"],
                            suggested_mode="template" if pattern_config["template_available"] else "structured_search"
                        )
        
        return best_match
    
    def _try_llm_routing(self, query: str) -> Optional[RouterResult]:
        """Level 2: LLM-basierte Klassifizierung"""
        try:
            # Build few-shot examples
            examples_text = "\n".join([
                f"Query: {ex[0]}\nIntent: {ex[1]}\n"
                for ex in self.llm_examples
            ])
            
            user_prompt = f"""Beispiele:
{examples_text}

Query: {query}
Intent:"""

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.llm_system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            predicted_intent = response.choices[0].message.content.strip()
            
            # Map to template availability
            template_intents = {
                "mieter_search_location", "mieter_contact_lookup", 
                "owner_search", "portfolio_query", "vacancy_status",
                "property_details", "account_balance"
            }
            
            template_available = predicted_intent in template_intents
            confidence = 0.8 if template_available else 0.6
            
            # Simple entity extraction for LLM results
            entities = self._simple_entity_extraction(query)
            
            return RouterResult(
                intent_id=predicted_intent,
                confidence=confidence,
                router_level="llm",
                processing_time_ms=0.0,  # Set later
                extracted_entities=entities,
                template_available=template_available,
                suggested_mode="template" if template_available else "structured_search"
            )
            
        except Exception as e:
            if self.debug_mode:
                print(f"   ⚠️  LLM Routing Error: {e}")
            return None
    
    def _simple_entity_extraction(self, query: str) -> Dict[str, str]:
        """Einfache Entity Extraction für LLM-Routing"""
        entities = {}
        query_lower = query.lower()
        
        # Person names
        person_patterns = [
            r"(?:herr|herrn|frau|familie)\s+([a-zA-ZäöüÄÖÜß\-\s]+?)(?:\s|$|,|\?)",
            r"von\s+([a-zA-ZäöüÄÖÜß\-\s]+?)(?:\s|$|,|\?)"
        ]
        for pattern in person_patterns:
            match = re.search(pattern, query_lower)
            if match:
                entities["person_name"] = match.group(1).strip()
                break
        
        # Locations
        location_patterns = [
            r"in\s+(?:der\s+)?([a-zA-ZäöüÄÖÜß\-\s]+straße?\s*\d*)",
            r"in\s+([a-zA-ZäöüÄÖÜß\-\s]+?)(?:\s|$|,|\?)"
        ]
        for pattern in location_patterns:
            match = re.search(pattern, query_lower)
            if match:
                entities["location"] = match.group(1).strip()
                break
        
        return entities
    
    def _fallback_routing(self, query: str) -> RouterResult:
        """Level 3: Fallback Routing (immer verfügbar)"""
        
        # Heuristic classification based on keywords
        if any(word in query.lower() for word in ["mieter", "bewohner", "wohnt"]):
            intent_id = "mieter_general"
            suggested_mode = "structured_search"
        elif any(word in query.lower() for word in ["eigentümer", "eigentuemer", "besitzer"]):
            intent_id = "owner_general"
            suggested_mode = "structured_search"
        elif any(word in query.lower() for word in ["objekt", "wohnung", "gebäude"]):
            intent_id = "property_general"
            suggested_mode = "structured_search"
        elif any(word in query.lower() for word in ["konto", "saldo", "zahlung"]):
            intent_id = "finance_general"
            suggested_mode = "structured_search"
        else:
            intent_id = "complex_general"
            suggested_mode = "legacy_json"
        
        return RouterResult(
            intent_id=intent_id,
            confidence=0.4,
            router_level="fallback",
            processing_time_ms=0.0,  # Set later
            extracted_entities=self._simple_entity_extraction(query),
            template_available=False,
            suggested_mode=suggested_mode
        )
    
    def route_batch(self, queries: List[str]) -> List[RouterResult]:
        """Batch-Processing für Performance-Tests"""
        results = []
        for query in queries:
            result = self.route_intent(query)
            results.append(result)
        return results
    
    def get_routing_stats(self, results: List[RouterResult]) -> Dict[str, Any]:
        """Analyse der Routing-Performance"""
        if not results:
            return {}
        
        level_counts = {}
        total_time = 0
        template_count = 0
        
        for result in results:
            level = result.router_level
            level_counts[level] = level_counts.get(level, 0) + 1
            total_time += result.processing_time_ms
            if result.template_available:
                template_count += 1
        
        return {
            "total_queries": len(results),
            "avg_processing_time_ms": round(total_time / len(results), 2),
            "routing_distribution": level_counts,
            "template_coverage": round(template_count / len(results) * 100, 1),
            "confidence_avg": round(sum(r.confidence for r in results) / len(results), 3)
        }

def test_hierarchical_router():
    """Test des Hierarchical Intent Routers"""
    print("🧪 Teste Hierarchical Intent Router...")
    
    router = HierarchicalIntentRouter(debug_mode=True)
    
    # Test queries (aus Golden Set)
    test_queries = [
        "Wer wohnt in der Bergstraße 15?",
        "Kontaktdaten von Herrn Müller", 
        "Zeige mir alle Mieter in Hamburg",
        "Portfolio von Familie Schmidt",
        "Freie Wohnungen in Köln",
        "Kontostand von Herr Weber",
        "Wie viele Objekte hat die Müller GmbH?",
        "Vermietungsgrad der Aachener Straße",
        "Mieter ohne Email-Adresse",
        "Bericht über alle Rückstände"
    ]
    
    print(f"\n📋 Routing Tests:")
    results = []
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        result = router.route_intent(query)
        results.append(result)
        
        print(f"   🎯 Intent: {result.intent_id}")
        print(f"   📊 Confidence: {result.confidence:.1%}")
        print(f"   🔧 Router Level: {result.router_level}")
        print(f"   ⏱️  Time: {result.processing_time_ms}ms")
        print(f"   🏷️  Entities: {result.extracted_entities}")
        print(f"   📝 Template: {result.template_available}")
        print(f"   🔄 Mode: {result.suggested_mode}")
    
    # Performance analysis
    print(f"\n📊 Routing Performance Analysis:")
    stats = router.get_routing_stats(results)
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Template coverage
    template_count = sum(1 for r in results if r.template_available)
    print(f"\n🎯 Template System Coverage:")
    print(f"   📝 {template_count}/{len(results)} Queries template-fähig ({template_count/len(results)*100:.1f}%)")
    print(f"   🔍 {len(results)-template_count} Queries brauchen Structured Search/Legacy")

if __name__ == "__main__":
    test_hierarchical_router()