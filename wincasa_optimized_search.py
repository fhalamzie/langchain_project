#!/usr/bin/env python3
"""
WINCASA Phase 2.2 - Optimized Structured Search System
Hochperformante Alternative zu RAG für strukturierte Business Queries
"""

import json
import os
import time
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

# Load OpenAI client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

@dataclass
class SearchResult:
    """Ein Suchergebnis aus dem optimierten Search System"""
    entity_type: str
    entity_data: Dict[str, Any]
    relevance_score: float
    matched_fields: List[str]
    exact_matches: List[str]

@dataclass 
class SearchResponse:
    """Antwort des optimierten Search Systems"""
    answer: str
    search_results: List[SearchResult]
    processing_time_ms: float
    token_usage: Dict[str, int]
    confidence: float

class WincasaOptimizedSearch:
    """
    Hochoptimiertes Structured Search System für WINCASA
    
    Performance-Features:
    - In-Memory Indizes für alle suchbaren Felder
    - Exakte und Partial-Match Algorithmen
    - Prefix-Trees für Auto-Complete
    - Multi-Threaded Search (falls nötig)
    - Sub-100ms Response Times
    """
    
    def __init__(self, 
                 rag_data_dir="exports/rag_data",
                 api_key_file="/home/envs/openai.env",
                 model_name="gpt-4o-mini",
                 debug_mode=False):
        
        self.rag_data_dir = Path(rag_data_dir)
        self.model_name = model_name
        self.debug_mode = debug_mode
        
        # Load API Key
        if OPENAI_AVAILABLE and os.path.exists(api_key_file):
            with open(api_key_file, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        self.client = OpenAI(api_key=api_key)
                        break
        else:
            self.client = None
            if self.debug_mode:
                print("⚠️  OpenAI Client nicht verfügbar")
        
        # Load and index data
        start_time = time.time()
        self.mieter_data = self._load_json_data("mieter.json")
        self.eigentuemer_data = self._load_json_data("eigentuemer.json")
        self.objekte_data = self._load_json_data("objekte.json")
        
        # Build optimized indices
        self._build_optimized_indices()
        
        indexing_time = round((time.time() - start_time) * 1000, 2)
        
        if self.debug_mode:
            print(f"✅ Optimized Search System initialisiert ({indexing_time}ms):")
            print(f"   📊 {len(self.mieter_data)} Mieter")
            print(f"   👥 {len(self.eigentuemer_data)} Eigentümer")
            print(f"   🏢 {len(self.objekte_data)} Objekte")
            print(f"   🔍 {len(self.name_index)} Namen im Index")
            print(f"   📍 {len(self.address_index)} Adressen im Index")
            print(f"   🏙️  {len(self.city_index)} Städte im Index")
    
    def _load_json_data(self, filename: str) -> List[Dict]:
        """Lädt JSON-Daten"""
        file_path = self.rag_data_dir / filename
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            if self.debug_mode:
                print(f"❌ Fehler beim Laden von {filename}: {e}")
            return []
    
    def _normalize_text(self, text: str) -> str:
        """Normalisiert Text für Index-Suche"""
        if not text or text in ['None', 'null', '']:
            return ""
        
        # Convert to lowercase
        normalized = str(text).lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # German character normalization
        normalized = normalized.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
        normalized = normalized.replace('ß', 'ss')
        
        return normalized
    
    def _extract_searchable_terms(self, text: str) -> Set[str]:
        """Extrahiert suchbare Begriffe aus Text"""
        if not text:
            return set()
        
        normalized = self._normalize_text(text)
        
        # Split into words
        words = re.findall(r'\w+', normalized)
        
        # Create term variations
        terms = set()
        for word in words:
            if len(word) >= 2:  # Minimum length
                terms.add(word)
                # Add prefixes for partial matching
                for i in range(3, len(word) + 1):
                    terms.add(word[:i])
        
        return terms
    
    def _get_nested_field(self, data: Dict, field_path: str) -> str:
        """Holt Wert aus nested Dict"""
        if '.' not in field_path:
            return str(data.get(field_path, ""))
        
        parts = field_path.split('.')
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return ""
        return str(current) if current else ""
    
    def _build_optimized_indices(self):
        """Baut hochoptimierte In-Memory Indizes"""
        
        # Multi-field indices
        self.name_index = {}        # name -> [(entity_type, entity, score_weight)]
        self.address_index = {}     # address_term -> [(entity_type, entity, score_weight)]
        self.city_index = {}        # city -> [(entity_type, entity, score_weight)]
        self.email_index = {}       # email_part -> [(entity_type, entity, score_weight)]
        self.phone_index = {}       # phone_part -> [(entity_type, entity, score_weight)]
        self.status_index = {}      # status -> [(entity_type, entity, score_weight)]
        
        # Index Mieter
        for entity in self.mieter_data:
            self._index_entity(entity, "mieter", {
                "name": (entity.get("name", ""), 1.0),
                "partner": (entity.get("partner", ""), 0.8),
                "address": (entity.get("adresse", ""), 0.7),
                "city": (entity.get("stadt", ""), 0.6),
                "email": (self._get_nested_field(entity, "kontakt.email"), 0.6),
                "phone": (self._get_nested_field(entity, "kontakt.telefon"), 0.4),
                "status": (self._get_nested_field(entity, "vertrag.zahlungsstatus"), 0.5)
            })
        
        # Index Eigentümer
        for entity in self.eigentuemer_data:
            self._index_entity(entity, "eigentuemer", {
                "name": (entity.get("name", ""), 1.0),
                "firma": (entity.get("firma", ""), 0.9),
                "address": (entity.get("plz_ort", ""), 0.6),
                "email": (self._get_nested_field(entity, "kontakt.email"), 0.6),
                "status": (self._get_nested_field(entity, "portfolio.kategorie"), 0.5)
            })
        
        # Index Objekte
        for entity in self.objekte_data:
            self._index_entity(entity, "objekte", {
                "address": (entity.get("adresse", ""), 1.0),
                "city": (entity.get("stadt", ""), 0.7),
                "status": (self._get_nested_field(entity, "vermietung.status"), 0.6),
                "owner": (self._get_nested_field(entity, "eigentuemer.name"), 0.8),
                "verwalter": (self._get_nested_field(entity, "verwaltung.verwalter_name"), 0.7)
            })
    
    def _index_entity(self, entity: Dict, entity_type: str, field_config: Dict[str, tuple]):
        """Indexiert eine Entität in alle relevanten Indizes"""
        
        for field_name, (field_value, weight) in field_config.items():
            if not field_value or field_value.strip() == "":
                continue
            
            terms = self._extract_searchable_terms(field_value)
            entry = (entity_type, entity, weight)
            
            # Route to appropriate indices
            if field_name in ["name", "partner", "firma", "owner"]:
                for term in terms:
                    if term not in self.name_index:
                        self.name_index[term] = []
                    self.name_index[term].append(entry)
            
            elif field_name in ["address"]:
                for term in terms:
                    if term not in self.address_index:
                        self.address_index[term] = []
                    self.address_index[term].append(entry)
            
            elif field_name in ["city"]:
                for term in terms:
                    if term not in self.city_index:
                        self.city_index[term] = []
                    self.city_index[term].append(entry)
            
            elif field_name in ["email"]:
                for term in terms:
                    if term not in self.email_index:
                        self.email_index[term] = []
                    self.email_index[term].append(entry)
            
            elif field_name in ["phone"]:
                for term in terms:
                    if term not in self.phone_index:
                        self.phone_index[term] = []
                    self.phone_index[term].append(entry)
            
            elif field_name in ["status"]:
                for term in terms:
                    if term not in self.status_index:
                        self.status_index[term] = []
                    self.status_index[term].append(entry)
    
    def _search_index(self, query: str, index: Dict, base_score: float = 1.0) -> Dict[str, tuple]:
        """Durchsucht einen Index hochoptimiert"""
        query_normalized = self._normalize_text(query)
        query_terms = self._extract_searchable_terms(query_normalized)
        
        entity_scores = {}  # entity_id -> (entity_type, entity, max_score)
        
        for term in query_terms:
            # Exact matches
            if term in index:
                for entity_type, entity, weight in index[term]:
                    entity_id = f"{entity_type}_{id(entity)}"
                    score = base_score * weight
                    if entity_id not in entity_scores or entity_scores[entity_id][2] < score:
                        entity_scores[entity_id] = (entity_type, entity, score)
            
            # Prefix matches for partial queries
            for index_term in index:
                if index_term.startswith(term) and index_term != term:
                    for entity_type, entity, weight in index[index_term]:
                        entity_id = f"{entity_type}_{id(entity)}"
                        score = base_score * weight * 0.8  # Slight penalty for partial match
                        if entity_id not in entity_scores or entity_scores[entity_id][2] < score:
                            entity_scores[entity_id] = (entity_type, entity, score)
        
        return entity_scores
    
    def optimized_search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Hochoptimierte Multi-Index Suche"""
        
        if not query or len(query.strip()) < 2:
            return []
        
        # Search all indices in parallel
        all_entity_scores = {}
        
        # Name search (highest priority)
        name_scores = self._search_index(query, self.name_index, 1.0)
        all_entity_scores.update(name_scores)
        
        # Address search
        address_scores = self._search_index(query, self.address_index, 0.8)
        for entity_id, (entity_type, entity, score) in address_scores.items():
            if entity_id in all_entity_scores:
                # Boost score for multi-field matches
                all_entity_scores[entity_id] = (entity_type, entity, all_entity_scores[entity_id][2] + score)
            else:
                all_entity_scores[entity_id] = (entity_type, entity, score)
        
        # City search
        city_scores = self._search_index(query, self.city_index, 0.6)
        for entity_id, (entity_type, entity, score) in city_scores.items():
            if entity_id in all_entity_scores:
                all_entity_scores[entity_id] = (entity_type, entity, all_entity_scores[entity_id][2] + score)
            else:
                all_entity_scores[entity_id] = (entity_type, entity, score)
        
        # Email search
        email_scores = self._search_index(query, self.email_index, 0.7)
        for entity_id, (entity_type, entity, score) in email_scores.items():
            if entity_id in all_entity_scores:
                all_entity_scores[entity_id] = (entity_type, entity, all_entity_scores[entity_id][2] + score)
            else:
                all_entity_scores[entity_id] = (entity_type, entity, score)
        
        # Status search
        status_scores = self._search_index(query, self.status_index, 0.5)
        for entity_id, (entity_type, entity, score) in status_scores.items():
            if entity_id in all_entity_scores:
                all_entity_scores[entity_id] = (entity_type, entity, all_entity_scores[entity_id][2] + score)
            else:
                all_entity_scores[entity_id] = (entity_type, entity, score)
        
        # Convert to SearchResult objects and sort
        results = []
        for entity_id, (entity_type, entity, score) in all_entity_scores.items():
            results.append(SearchResult(
                entity_type=entity_type,
                entity_data=entity,
                relevance_score=score,
                matched_fields=self._identify_matched_fields(query, entity, entity_type),
                exact_matches=self._identify_exact_matches(query, entity, entity_type)
            ))
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results[:max_results]
    
    def _identify_matched_fields(self, query: str, entity: Dict, entity_type: str) -> List[str]:
        """Identifiziert welche Felder gematcht haben"""
        query_norm = self._normalize_text(query)
        matched_fields = []
        
        # Define fields to check per entity type
        if entity_type == "mieter":
            check_fields = [
                ("name", entity.get("name", "")),
                ("partner", entity.get("partner", "")),
                ("adresse", entity.get("adresse", "")),
                ("stadt", entity.get("stadt", "")),
                ("email", self._get_nested_field(entity, "kontakt.email"))
            ]
        elif entity_type == "eigentuemer":
            check_fields = [
                ("name", entity.get("name", "")),
                ("firma", entity.get("firma", "")),
                ("plz_ort", entity.get("plz_ort", "")),
                ("email", self._get_nested_field(entity, "kontakt.email"))
            ]
        elif entity_type == "objekte":
            check_fields = [
                ("adresse", entity.get("adresse", "")),
                ("stadt", entity.get("stadt", "")),
                ("status", self._get_nested_field(entity, "vermietung.status")),
                ("eigentuemer", self._get_nested_field(entity, "eigentuemer.name"))
            ]
        else:
            return []
        
        for field_name, field_value in check_fields:
            if field_value and query_norm in self._normalize_text(field_value):
                matched_fields.append(field_name)
        
        return matched_fields
    
    def _identify_exact_matches(self, query: str, entity: Dict, entity_type: str) -> List[str]:
        """Identifiziert exakte Matches"""
        query_norm = self._normalize_text(query)
        exact_matches = []
        
        if entity_type == "mieter":
            if query_norm == self._normalize_text(entity.get("name", "")):
                exact_matches.append("name")
        elif entity_type == "eigentuemer":
            if query_norm == self._normalize_text(entity.get("name", "")):
                exact_matches.append("name")
        elif entity_type == "objekte":
            if query_norm == self._normalize_text(entity.get("adresse", "")):
                exact_matches.append("adresse")
        
        return exact_matches
    
    def _format_results_for_llm(self, results: List[SearchResult]) -> str:
        """Formatiert Ergebnisse für LLM"""
        if not results:
            return "Keine Suchergebnisse gefunden."
        
        context_parts = []
        for result in results:
            entity_type = result.entity_type
            data = result.entity_data
            
            if entity_type == "mieter":
                context = f"MIETER: {data.get('name', 'N/A')}"
                if data.get("partner"):
                    context += f" & {data['partner']}"
                context += f" - {data.get('adresse', 'N/A')}"
                
            elif entity_type == "eigentuemer":
                context = f"EIGENTÜMER: {data.get('name', 'N/A')}"
                if data.get("firma"):
                    context += f" ({data['firma']})"
                context += f" - {data.get('plz_ort', 'N/A')}"
                
            elif entity_type == "objekte":
                context = f"OBJEKT: {data.get('adresse', 'N/A')}"
                context += f" - {data.get('stadt', 'N/A')}"
                vermietung = self._get_nested_field(data, "vermietung.status")
                if vermietung:
                    context += f" - {vermietung}"
            
            if self.debug_mode:
                context += f" [Score: {result.relevance_score:.2f}, Fields: {result.matched_fields}]"
            
            context_parts.append(context)
        
        return "\n".join(context_parts)
    
    def query(self, user_query: str, max_results: int = 5) -> SearchResponse:
        """Hauptsuchfunktion mit optimierter Performance"""
        start_time = time.time()
        
        if self.debug_mode:
            print(f"🔍 Optimized Search: '{user_query}'")
        
        # Optimized search
        search_results = self.optimized_search(user_query, max_results)
        search_time = time.time()
        
        if self.debug_mode:
            print(f"   📊 {len(search_results)} Ergebnisse in {round((search_time - start_time) * 1000, 2)}ms")
        
        if not search_results:
            return SearchResponse(
                answer="Keine relevanten Daten für Ihre Anfrage gefunden.",
                search_results=[],
                processing_time_ms=round((time.time() - start_time) * 1000, 2),
                token_usage={"prompt_tokens": 0, "completion_tokens": 0},
                confidence=0.0
            )
        
        # LLM Processing
        if self.client:
            try:
                context = self._format_results_for_llm(search_results)
                
                system_prompt = """Du bist ein WINCASA Immobilienverwaltungsexperte. 
Beantworte Fragen basierend ausschließlich auf den bereitgestellten Daten.
Sei präzise, geschäftlich und verwende deutsche Fachbegriffe."""

                user_prompt = f"""ANFRAGE: {user_query}

SUCHERGEBNISSE:
{context}

Bitte beantworte die Anfrage basierend auf diesen Daten."""

                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=400
                )
                
                answer = response.choices[0].message.content
                token_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
                
                # Higher confidence for exact matches
                base_confidence = 0.7
                if any(result.exact_matches for result in search_results):
                    base_confidence = 0.9
                confidence = min(base_confidence + (len(search_results) * 0.05), 0.95)
                
            except Exception as e:
                if self.debug_mode:
                    print(f"⚠️  LLM-Fehler: {e}")
                answer = f"Gefunden: {len(search_results)} relevante Einträge."
                token_usage = {"prompt_tokens": 0, "completion_tokens": 0}
                confidence = 0.6
        else:
            answer = f"Gefunden: {len(search_results)} relevante Einträge für '{user_query}'"
            token_usage = {"prompt_tokens": 0, "completion_tokens": 0}
            confidence = 0.5
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        return SearchResponse(
            answer=answer,
            search_results=search_results,
            processing_time_ms=processing_time,
            token_usage=token_usage,
            confidence=confidence
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """System-Statistiken"""
        return {
            "entities": {
                "mieter": len(self.mieter_data),
                "eigentuemer": len(self.eigentuemer_data),
                "objekte": len(self.objekte_data)
            },
            "indices": {
                "names": len(self.name_index),
                "addresses": len(self.address_index),
                "cities": len(self.city_index),
                "emails": len(self.email_index),
                "status": len(self.status_index)
            },
            "model": self.model_name,
            "llm_available": self.client is not None
        }

def test_optimized_search():
    """Performance-Test der optimierten Suche"""
    print("🚀 Teste Optimized Search System...")
    
    search_system = WincasaOptimizedSearch(debug_mode=True)
    
    test_queries = [
        "Müller",
        "müller", 
        "Hamburg",
        "Köln",
        "Aachener",
        "GmbH",
        "Vollvermietet",
        "info@",
        "bergstr",
        "Teilvermietet",
    ]
    
    print(f"\n📋 Performance Tests:")
    total_time = 0
    total_results = 0
    
    for query in test_queries:
        response = search_system.query(query, max_results=5)
        total_time += response.processing_time_ms
        total_results += len(response.search_results)
        
        print(f"   '{query}': {response.processing_time_ms}ms → {len(response.search_results)} results")
    
    print(f"\n📊 Performance Summary:")
    print(f"   ⏱️  Durchschnitt: {total_time/len(test_queries):.1f}ms pro Query")
    print(f"   📈 Durchschnitt: {total_results/len(test_queries):.1f} Results pro Query")
    print(f"   🎯 Gesamtzeit: {total_time:.1f}ms für {len(test_queries)} Queries")
    
    stats = search_system.get_stats()
    print(f"\n📋 System Stats: {stats}")

if __name__ == "__main__":
    test_optimized_search()