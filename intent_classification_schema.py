#!/usr/bin/env python3
"""
WINCASA Phase 2.3 - Intent Classification Schema
Hierarchisches Intent-System basierend auf Golden Set Analysis
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum

class IntentLevel(Enum):
    """Intent-Hierarchie Levels"""
    PRIMARY = "primary"      # Hauptkategorie (Mieter, Eigentümer, Objekt, etc.)
    SECONDARY = "secondary"  # Aktion (Suchen, Analysieren, Berichten)
    TERTIARY = "tertiary"    # Spezifisch (Kontaktdaten, Zahlungen, Leerstand)

@dataclass
class IntentPattern:
    """Ein Intent-Erkennungsmuster"""
    intent_id: str
    keywords: List[str]
    regex_patterns: List[str]
    required_entities: List[str]  # Name, Adresse, PLZ, etc.
    confidence_weight: float
    template_available: bool

@dataclass
class IntentResult:
    """Ergebnis der Intent-Klassifizierung"""
    primary_intent: str
    secondary_intent: str
    tertiary_intent: Optional[str]
    confidence: float
    matched_patterns: List[str]
    extracted_entities: Dict[str, str]
    template_id: Optional[str]
    fallback_mode: str  # "structured_search", "legacy_json", "complex_query"

class WincasaIntentClassifier:
    """
    WINCASA Intent Classification System
    
    Hierarchische Klassifizierung:
    Level 1: Primary Intent (Mieter, Eigentümer, Objekt, Finanzen, Admin)
    Level 2: Secondary Intent (Suchen, Analysieren, Berichten, Bearbeiten)
    Level 3: Tertiary Intent (Kontakt, Zahlungen, Portfolio, etc.)
    """
    
    def __init__(self, golden_set_path: str = "golden_set/queries.json"):
        self.golden_set_path = Path(golden_set_path)
        
        # Load golden set for validation
        self.golden_queries = self._load_golden_set()
        
        # Initialize intent patterns
        self.intent_patterns = self._build_intent_patterns()
        
        print(f"✅ Intent Classifier initialisiert:")
        print(f"   📋 {len(self.intent_patterns)} Intent-Patterns")
        print(f"   🎯 {len(self.golden_queries)} Golden Set Queries für Validation")
    
    def _load_golden_set(self) -> List[Dict]:
        """Lädt Golden Set für Validation"""
        if not self.golden_set_path.exists():
            return []
        
        try:
            with open(self.golden_set_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('queries', [])
        except Exception as e:
            print(f"⚠️  Golden Set laden fehlgeschlagen: {e}")
            return []
    
    def _build_intent_patterns(self) -> Dict[str, IntentPattern]:
        """Erstellt Intent-Erkennungspatterns basierend auf Golden Set"""
        patterns = {}
        
        # === PRIMARY INTENT: MIETER ===
        
        # Mieter Suche
        patterns["mieter_search"] = IntentPattern(
            intent_id="mieter_search",
            keywords=["mieter", "bewohner", "wohnt", "mieterin", "bewohnerin"],
            regex_patterns=[
                r"wer\s+wohnt\s+in",
                r"zeige.*mieter.*in",
                r"mieter.*in\s+\w+",
                r"bewohner.*von"
            ],
            required_entities=["location"],  # Adresse oder Stadt
            confidence_weight=1.0,
            template_available=True
        )
        
        # Mieter Kontakt
        patterns["mieter_contact"] = IntentPattern(
            intent_id="mieter_contact",
            keywords=["kontakt", "telefon", "email", "adresse", "kontaktdaten"],
            regex_patterns=[
                r"kontakt.*von",
                r"telefon.*von",
                r"email.*von", 
                r"kontaktdaten.*von"
            ],
            required_entities=["person_name"],
            confidence_weight=1.0,
            template_available=True
        )
        
        # Mieter Zahlungen
        patterns["mieter_payments"] = IntentPattern(
            intent_id="mieter_payments",
            keywords=["zahlung", "miete", "saldo", "schulden", "rückstand", "guthaben"],
            regex_patterns=[
                r"zahlung.*von",
                r"saldo.*von",
                r"schulden.*von",
                r"rückstand.*von"
            ],
            required_entities=["person_name"],
            confidence_weight=0.9,
            template_available=True
        )
        
        # === PRIMARY INTENT: EIGENTÜMER ===
        
        # Eigentümer Suche
        patterns["owner_search"] = IntentPattern(
            intent_id="owner_search",
            keywords=["eigentümer", "eigentuemer", "besitzer", "owner"],
            regex_patterns=[
                r"eigentümer.*von",
                r"eigentuemer.*von",
                r"wem.*gehört",
                r"besitzer.*von"
            ],
            required_entities=["location"],
            confidence_weight=1.0,
            template_available=True
        )
        
        # Portfolio Analyse
        patterns["portfolio_analysis"] = IntentPattern(
            intent_id="portfolio_analysis",
            keywords=["portfolio", "objekte", "besitz", "mehrere", "anzahl"],
            regex_patterns=[
                r"portfolio.*von",
                r"wie\s+viele.*objekte",
                r"anzahl.*objekte",
                r"besitz.*von"
            ],
            required_entities=["person_name"],
            confidence_weight=0.8,
            template_available=True
        )
        
        # === PRIMARY INTENT: OBJEKT ===
        
        # Objekt Details
        patterns["property_details"] = IntentPattern(
            intent_id="property_details",
            keywords=["objekt", "gebäude", "haus", "wohnung", "einheiten"],
            regex_patterns=[
                r"details.*zu",
                r"info.*über.*objekt",
                r"wie\s+viele\s+wohnungen",
                r"einheiten.*in"
            ],
            required_entities=["location"],
            confidence_weight=0.9,
            template_available=True
        )
        
        # Leerstand
        patterns["vacancy_status"] = IntentPattern(
            intent_id="vacancy_status",
            keywords=["leer", "leerstand", "frei", "vermietung", "vermietet"],
            regex_patterns=[
                r"leerstand.*in",
                r"freie.*wohnungen",
                r"vermietungsgrad",
                r"wie\s+viele.*leer"
            ],
            required_entities=["location"],
            confidence_weight=0.9,
            template_available=True
        )
        
        # === PRIMARY INTENT: FINANZEN ===
        
        # Kontostand
        patterns["account_balance"] = IntentPattern(
            intent_id="account_balance",
            keywords=["konto", "saldo", "kontostand", "guthaben", "schulden"],
            regex_patterns=[
                r"kontostand.*von",
                r"saldo.*von",
                r"guthaben.*von",
                r"schulden.*von"
            ],
            required_entities=["person_name"],
            confidence_weight=0.9,
            template_available=True
        )
        
        # Rücklagen
        patterns["reserves"] = IntentPattern(
            intent_id="reserves",
            keywords=["rücklage", "ruecklage", "reserve", "rückstellung"],
            regex_patterns=[
                r"rücklage.*von",
                r"ruecklage.*von",
                r"reserve.*für",
                r"rückstellung.*für"
            ],
            required_entities=["location"],
            confidence_weight=0.8,
            template_available=False
        )
        
        # === COMPLEX QUERIES (Fallback to Legacy) ===
        
        # Reports & Analytics
        patterns["complex_analysis"] = IntentPattern(
            intent_id="complex_analysis",
            keywords=["analyse", "bericht", "übersicht", "statistik", "vergleich"],
            regex_patterns=[
                r"erstelle.*bericht",
                r"analyse.*über",
                r"übersicht.*über",
                r"statistik.*für"
            ],
            required_entities=[],
            confidence_weight=0.6,
            template_available=False
        )
        
        # === ADMIN QUERIES ===
        
        # WEG Verwaltung
        patterns["weg_administration"] = IntentPattern(
            intent_id="weg_administration", 
            keywords=["beirat", "beiräte", "versammlung", "beschluss", "weg"],
            regex_patterns=[
                r"beirat.*für",
                r"versammlung.*am",
                r"beschluss.*vom",
                r"weg.*verwaltung"
            ],
            required_entities=[],
            confidence_weight=0.7,
            template_available=False
        )
        
        return patterns
    
    def classify_intent(self, query: str) -> IntentResult:
        """
        Klassifiziert Query-Intent mit hierarchischem Ansatz
        
        Stufe 1: Keyword & Regex Matching (hochpräzise)
        Stufe 2: Pattern-Scoring mit Entitäten
        Stufe 3: Fallback-Bestimmung
        """
        query_lower = query.lower().strip()
        
        # Stufe 1: Pattern Matching
        pattern_scores = {}
        for pattern_id, pattern in self.intent_patterns.items():
            score = self._calculate_pattern_score(query_lower, pattern)
            if score > 0:
                pattern_scores[pattern_id] = score
        
        # Stufe 2: Beste Patterns finden
        if not pattern_scores:
            return self._create_fallback_result(query, "no_patterns_matched")
        
        # Sort by score
        sorted_patterns = sorted(pattern_scores.items(), key=lambda x: x[1], reverse=True)
        best_pattern_id, best_score = sorted_patterns[0]
        best_pattern = self.intent_patterns[best_pattern_id]
        
        # Stufe 3: Entity Extraction
        extracted_entities = self._extract_entities(query_lower, best_pattern.required_entities)
        
        # Stufe 4: Intent-Hierarchie bestimmen
        primary, secondary, tertiary = self._determine_intent_hierarchy(best_pattern_id)
        
        # Stufe 5: Template vs. Fallback
        if best_pattern.template_available and best_score >= 0.7:
            template_id = f"template_{best_pattern_id}"
            fallback_mode = "template"
        elif best_score >= 0.5:
            template_id = None
            fallback_mode = "structured_search"
        else:
            template_id = None
            fallback_mode = "legacy_json"
        
        return IntentResult(
            primary_intent=primary,
            secondary_intent=secondary,
            tertiary_intent=tertiary,
            confidence=min(best_score, 0.95),
            matched_patterns=[best_pattern_id],
            extracted_entities=extracted_entities,
            template_id=template_id,
            fallback_mode=fallback_mode
        )
    
    def _calculate_pattern_score(self, query: str, pattern: IntentPattern) -> float:
        """Berechnet Pattern-Match Score"""
        score = 0.0
        
        # Keyword matching
        keyword_matches = 0
        for keyword in pattern.keywords:
            if keyword.lower() in query:
                keyword_matches += 1
        
        if keyword_matches > 0:
            score += (keyword_matches / len(pattern.keywords)) * 0.6
        
        # Regex matching  
        regex_matches = 0
        for regex_pattern in pattern.regex_patterns:
            if re.search(regex_pattern, query):
                regex_matches += 1
        
        if regex_matches > 0:
            score += (regex_matches / len(pattern.regex_patterns)) * 0.4
        
        # Weight by pattern confidence
        return score * pattern.confidence_weight
    
    def _extract_entities(self, query: str, required_entities: List[str]) -> Dict[str, str]:
        """Einfache Entity Extraction für deutsche Texte"""
        entities = {}
        
        # Person names (Herr/Frau + Name)
        if "person_name" in required_entities:
            name_patterns = [
                r"(?:herr|herrn|frau|familie)\s+([a-zA-ZäöüÄÖÜß\-\s]+?)(?:\s|$|,|\?)",
                r"von\s+([a-zA-ZäöüÄÖÜß\-\s]+?)(?:\s|$|,|\?)",
                r"([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*?)(?:\s+wohnt|\s+in|\s|$)"
            ]
            for pattern in name_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    entities["person_name"] = match.group(1).strip()
                    break
        
        # Locations (Straße, Stadt, PLZ)
        if "location" in required_entities:
            location_patterns = [
                r"in\s+der\s+([a-zA-ZäöüÄÖÜß\-\s]+straße?\s*\d*)",
                r"in\s+([a-zA-ZäöüÄÖÜß\-\s]+straße?\s*\d*)",
                r"straße?\s+(\d+)",
                r"in\s+([a-zA-ZäöüÄÖÜß\-\s]+?)(?:\s|$|,|\?)",
                r"(\d{5})\s+([a-zA-ZäöüÄÖÜß\-\s]+)"
            ]
            for pattern in location_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    entities["location"] = match.group(1).strip() if match.group(1) else match.group(0).strip()
                    break
        
        return entities
    
    def _determine_intent_hierarchy(self, pattern_id: str) -> Tuple[str, str, Optional[str]]:
        """Bestimmt Intent-Hierarchie basierend auf Pattern ID"""
        
        # Intent mapping
        hierarchy_map = {
            "mieter_search": ("mieter", "search", "location_based"),
            "mieter_contact": ("mieter", "lookup", "contact_info"),
            "mieter_payments": ("mieter", "analysis", "financial"),
            "owner_search": ("eigentuemer", "search", "property_based"),
            "portfolio_analysis": ("eigentuemer", "analysis", "portfolio"),
            "property_details": ("objekt", "lookup", "details"),
            "vacancy_status": ("objekt", "analysis", "occupancy"),
            "account_balance": ("finanzen", "lookup", "balance"),
            "reserves": ("finanzen", "lookup", "reserves"),
            "complex_analysis": ("admin", "analysis", "reporting"),
            "weg_administration": ("admin", "lookup", "weg")
        }
        
        return hierarchy_map.get(pattern_id, ("unknown", "unknown", None))
    
    def _create_fallback_result(self, query: str, reason: str) -> IntentResult:
        """Erstellt Fallback-Result für unklassifizierte Queries"""
        return IntentResult(
            primary_intent="unknown",
            secondary_intent="unknown", 
            tertiary_intent=None,
            confidence=0.3,
            matched_patterns=[],
            extracted_entities={},
            template_id=None,
            fallback_mode="legacy_json"
        )
    
    def validate_with_golden_set(self) -> Dict[str, float]:
        """Validiert Classifier gegen Golden Set"""
        if not self.golden_queries:
            return {"error": "No golden set available"}
        
        correct_classifications = 0
        total_queries = len(self.golden_queries)
        
        classification_results = []
        
        for golden_query in self.golden_queries[:20]:  # Test first 20
            query_text = golden_query.get("query", "")
            expected_category = golden_query.get("category", "")
            expected_intent = golden_query.get("intent", "")
            
            # Classify with our system
            result = self.classify_intent(query_text)
            
            # Simple validation: check if primary intent matches expected category
            matches_category = expected_category in result.primary_intent or result.primary_intent in expected_category
            
            if matches_category and result.confidence > 0.6:
                correct_classifications += 1
            
            classification_results.append({
                "query": query_text,
                "expected": expected_category,
                "predicted": result.primary_intent,
                "confidence": result.confidence,
                "correct": matches_category
            })
        
        accuracy = correct_classifications / min(total_queries, 20)
        
        return {
            "accuracy": accuracy,
            "correct": correct_classifications,
            "total": min(total_queries, 20),
            "details": classification_results
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """System-Statistiken"""
        template_patterns = sum(1 for p in self.intent_patterns.values() if p.template_available)
        
        return {
            "total_patterns": len(self.intent_patterns),
            "template_patterns": template_patterns,
            "fallback_patterns": len(self.intent_patterns) - template_patterns,
            "golden_queries": len(self.golden_queries),
            "primary_intents": len(set(self._determine_intent_hierarchy(pid)[0] for pid in self.intent_patterns.keys()))
        }

def test_intent_classifier():
    """Test des Intent Classification Systems"""
    print("🧪 Teste WINCASA Intent Classifier...")
    
    classifier = WincasaIntentClassifier()
    
    # Test queries
    test_queries = [
        "Wer wohnt in der Bergstraße 15?",
        "Kontaktdaten von Herrn Müller",
        "Zeige mir alle Mieter in Hamburg", 
        "Portfolio von Eigentümer Schmidt",
        "Leerstand in Köln",
        "Kontostand von Familie Weber",
        "Wie viele Objekte hat Müller GmbH?",
        "Vermietungsgrad Aachener Straße",
        "Rücklagen für WEG Musterstraße"
    ]
    
    print(f"\n📋 Test Classification:")
    for query in test_queries:
        result = classifier.classify_intent(query)
        print(f"\n🔍 Query: '{query}'")
        print(f"   🎯 Intent: {result.primary_intent} → {result.secondary_intent} → {result.tertiary_intent}")
        print(f"   📊 Confidence: {result.confidence:.1%}")
        print(f"   🏷️  Entities: {result.extracted_entities}")
        print(f"   📝 Template: {result.template_id or 'None'}")
        print(f"   🔄 Fallback: {result.fallback_mode}")
    
    # Golden Set Validation
    print(f"\n📊 Golden Set Validation:")
    validation_results = classifier.validate_with_golden_set()
    print(f"   🎯 Accuracy: {validation_results.get('accuracy', 0):.1%}")
    print(f"   ✅ Correct: {validation_results.get('correct', 0)}/{validation_results.get('total', 0)}")
    
    # System stats
    stats = classifier.get_stats()
    print(f"\n📋 System Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    test_intent_classifier()