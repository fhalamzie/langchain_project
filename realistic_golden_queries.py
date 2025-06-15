#!/usr/bin/env python3
"""
WINCASA Phase 2.3 - Realistic Golden Set Generator
Erstellt realistische Test-Queries basierend auf echten Datenbankwerten
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Set
from wincasa_optimized_search import WincasaOptimizedSearch

class RealisticGoldenSetGenerator:
    """
    Generiert realistische Test-Queries basierend auf echten WINCASA-Daten
    
    Warum wichtig:
    - Performance-Tests mit echten Datenmengen
    - Template-Validation mit realen Parametern  
    - Hit Rate Analysis mit echten Verteilungen
    - Entity Extraction mit komplexen deutschen Namen
    """
    
    def __init__(self):
        # Load real data
        self.search_system = WincasaOptimizedSearch()
        
        # Extract real values
        self.real_cities = self._extract_cities()
        self.real_addresses = self._extract_addresses()
        self.real_names = self._extract_names()
        self.real_companies = self._extract_companies()
        
        print(f"✅ Realistic Golden Set Generator initialisiert:")
        print(f"   🏙️  {len(self.real_cities)} echte Städte")
        print(f"   🏠 {len(self.real_addresses)} echte Adressen")
        print(f"   👥 {len(self.real_names)} echte Namen")
        print(f"   🏢 {len(self.real_companies)} echte Firmen")
    
    def _extract_cities(self) -> Set[str]:
        """Extrahiert echte Städte aus der Datenbank"""
        cities = set()
        
        # Mieter-Städte
        for mieter in self.search_system.mieter_data:
            stadt = mieter.get('stadt', '').strip()
            if stadt and len(stadt) > 2:
                cities.add(stadt)
        
        # Objekt-Städte
        for objekt in self.search_system.objekte_data:
            stadt = objekt.get('stadt', '').strip()
            if stadt and len(stadt) > 2:
                cities.add(stadt)
        
        # Eigentümer-Städte (aus PLZ_ORT)
        for eigentuemer in self.search_system.eigentuemer_data:
            plz_ort = eigentuemer.get('plz_ort') or ''
            if isinstance(plz_ort, str) and plz_ort.strip() and ' ' in plz_ort:
                stadt = plz_ort.split()[-1]  # Letztes Wort = Stadt
                if len(stadt) > 2:
                    cities.add(stadt)
        
        return cities
    
    def _extract_addresses(self) -> Set[str]:
        """Extrahiert echte Adressen"""
        addresses = set()
        
        # Mieter-Adressen (Objekt-Adressen)
        for mieter in self.search_system.mieter_data:
            adresse = mieter.get('adresse', '').strip()
            if adresse and len(adresse) > 5:
                # Extract street name (vor der Komma)
                street = adresse.split(',')[0].strip()
                if len(street) > 5:
                    addresses.add(street)
        
        # Objekt-Adressen
        for objekt in self.search_system.objekte_data:
            adresse = objekt.get('adresse', '').strip()
            if adresse and len(adresse) > 5:
                addresses.add(adresse)
        
        return addresses
    
    def _extract_names(self) -> Set[str]:
        """Extrahiert echte Personennamen (ohne Firmen)"""
        names = set()
        
        # Mieter-Namen
        for mieter in self.search_system.mieter_data:
            name = mieter.get('name') or ''
            if isinstance(name, str) and name.strip() and len(name) > 2:
                # Filter out companies (GmbH, e.V., etc.)
                if not any(x in name for x in ['GmbH', 'e.V.', 'KG', 'AG', 'UG']):
                    # Extract family names
                    parts = name.split()
                    for part in parts:
                        if len(part) > 3 and part[0].isupper():
                            names.add(part)
        
        # Eigentümer-Namen
        for eigentuemer in self.search_system.eigentuemer_data:
            name = eigentuemer.get('name') or ''
            if isinstance(name, str) and name.strip() and len(name) > 2:
                if not any(x in name for x in ['GmbH', 'e.V.', 'KG', 'AG', 'UG']):
                    parts = name.split()
                    for part in parts:
                        if len(part) > 3 and part[0].isupper() and part not in ['WEG', 'Herr', 'Frau']:
                            names.add(part)
        
        return names
    
    def _extract_companies(self) -> Set[str]:
        """Extrahiert echte Firmennamen"""
        companies = set()
        
        # Mieter-Firmen
        for mieter in self.search_system.mieter_data:
            name = mieter.get('name') or ''
            if isinstance(name, str) and name.strip() and any(x in name for x in ['GmbH', 'e.V.', 'KG', 'AG', 'UG']):
                companies.add(name.strip())
        
        # Eigentümer-Firmen
        for eigentuemer in self.search_system.eigentuemer_data:
            name = eigentuemer.get('name') or ''
            if isinstance(name, str) and name.strip() and any(x in name for x in ['GmbH', 'e.V.', 'KG', 'AG', 'UG']):
                companies.add(name.strip())
            
            firma = eigentuemer.get('firma') or ''
            if isinstance(firma, str) and firma.strip() and len(firma) > 3:
                companies.add(firma.strip())
        
        return companies
    
    def generate_realistic_queries(self, num_queries: int = 50) -> List[Dict]:
        """Generiert realistische Test-Queries mit echten Datenbankwerten"""
        
        queries = []
        
        # Template für verschiedene Query-Typen
        query_templates = [
            # Mieter-Searches (mit echten Adressen)
            {
                "template": "Wer wohnt in der {address}?",
                "intent": "lookup",
                "category": "mieter_search",
                "data_source": "addresses",
                "weight": 0.15
            },
            {
                "template": "Zeige mir alle Mieter in {city}",
                "intent": "lookup", 
                "category": "mieter_search",
                "data_source": "cities",
                "weight": 0.10
            },
            
            # Kontakt-Lookups (mit echten Namen)
            {
                "template": "Kontaktdaten von {name}",
                "intent": "lookup",
                "category": "contact_lookup",
                "data_source": "names",
                "weight": 0.15
            },
            {
                "template": "Telefonnummer von Familie {name}",
                "intent": "lookup",
                "category": "contact_lookup", 
                "data_source": "names",
                "weight": 0.10
            },
            
            # Portfolio-Queries (mit echten Firmen)
            {
                "template": "Portfolio von {company}",
                "intent": "template",
                "category": "portfolio_query",
                "data_source": "companies",
                "weight": 0.08
            },
            {
                "template": "Wie viele Objekte hat {company}?",
                "intent": "template",
                "category": "portfolio_query",
                "data_source": "companies", 
                "weight": 0.07
            },
            
            # Leerstand-Queries (mit echten Städten)
            {
                "template": "Freie Wohnungen in {city}",
                "intent": "template",
                "category": "vacancy_status",
                "data_source": "cities",
                "weight": 0.10
            },
            {
                "template": "Leerstand in {city}",
                "intent": "template", 
                "category": "vacancy_status",
                "data_source": "cities",
                "weight": 0.08
            },
            
            # Objekt-Details (mit echten Adressen)
            {
                "template": "Details zu {address}",
                "intent": "template",
                "category": "property_details",
                "data_source": "addresses",
                "weight": 0.07
            },
            
            # Finanz-Queries (mit echten Namen)
            {
                "template": "Kontostand von {name}",
                "intent": "template",
                "category": "account_balance",
                "data_source": "names",
                "weight": 0.10
            }
        ]
        
        # Generate queries based on weights
        for template_config in query_templates:
            num_for_template = int(num_queries * template_config["weight"])
            
            for _ in range(num_for_template):
                # Select random real value
                data_source = template_config["data_source"]
                if data_source == "cities":
                    value = random.choice(list(self.real_cities))
                elif data_source == "addresses":
                    value = random.choice(list(self.real_addresses))
                elif data_source == "names":
                    value = random.choice(list(self.real_names))
                elif data_source == "companies":
                    value = random.choice(list(self.real_companies))
                else:
                    continue
                
                # Generate query
                query_text = template_config["template"].format(**{
                    "address": value,
                    "city": value,
                    "name": value,
                    "company": value
                })
                
                queries.append({
                    "id": f"realistic_{len(queries)+1:03d}",
                    "query": query_text,
                    "category": template_config["category"],
                    "intent": template_config["intent"],
                    "expected_data": self._determine_expected_data(template_config["category"]),
                    "real_value": value,
                    "data_source": data_source
                })
        
        return queries
    
    def _determine_expected_data(self, category: str) -> str:
        """Bestimmt erwartete Datenquelle basierend auf Kategorie"""
        mapping = {
            "mieter_search": "mieter_komplett",
            "contact_lookup": "mieter_komplett", 
            "portfolio_query": "eigentuemer_portfolio",
            "vacancy_status": "objekte_details",
            "property_details": "objekte_details",
            "account_balance": "mieter_komplett"
        }
        return mapping.get(category, "complex_query")
    
    def validate_with_search_system(self, queries: List[Dict]) -> Dict[str, any]:
        """Validiert Queries gegen echtes Suchsystem"""
        results = {
            "total_queries": len(queries),
            "queries_with_results": 0,
            "avg_results_per_query": 0,
            "zero_result_queries": [],
            "high_result_queries": [],
            "performance_samples": []
        }
        
        total_results = 0
        
        for query_data in queries[:10]:  # Sample 10 für Performance
            query_text = query_data["query"]
            
            # Test mit Search System
            search_response = self.search_system.query(query_text, max_results=10)
            num_results = len(search_response.search_results)
            
            total_results += num_results
            if num_results > 0:
                results["queries_with_results"] += 1
            
            if num_results == 0:
                results["zero_result_queries"].append({
                    "query": query_text,
                    "real_value": query_data["real_value"],
                    "category": query_data["category"]
                })
            elif num_results >= 5:
                results["high_result_queries"].append({
                    "query": query_text,
                    "results": num_results,
                    "category": query_data["category"]
                })
            
            results["performance_samples"].append({
                "query": query_text,
                "results": num_results,
                "time_ms": search_response.processing_time_ms,
                "confidence": search_response.confidence
            })
        
        results["avg_results_per_query"] = total_results / len(results["performance_samples"])
        results["hit_rate"] = results["queries_with_results"] / len(results["performance_samples"])
        
        return results
    
    def save_realistic_golden_set(self, filename: str = "realistic_golden_set.json"):
        """Speichert realistisches Golden Set"""
        queries = self.generate_realistic_queries(50)
        
        # Validation
        validation_results = self.validate_with_search_system(queries)
        
        golden_set = {
            "meta": {
                "version": "2.0_realistic", 
                "created": "2025-06-14",
                "total_queries": len(queries),
                "description": "WINCASA Realistic Golden Set mit echten Datenbankwerten",
                "validation": validation_results,
                "real_data_stats": {
                    "cities": len(self.real_cities),
                    "addresses": len(self.real_addresses), 
                    "names": len(self.real_names),
                    "companies": len(self.real_companies)
                }
            },
            "queries": queries
        }
        
        output_path = Path(filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(golden_set, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Realistic Golden Set gespeichert: {output_path}")
        print(f"📊 Validation Results:")
        print(f"   ✅ Hit Rate: {validation_results['hit_rate']:.1%}")
        print(f"   📈 Avg Results: {validation_results['avg_results_per_query']:.1f}")
        print(f"   ❌ Zero Results: {len(validation_results['zero_result_queries'])}")
        
        return golden_set

def main():
    """Generiert und testet realistisches Golden Set"""
    print("🎯 Generiere Realistic Golden Set mit echten WINCASA-Daten...")
    
    generator = RealisticGoldenSetGenerator()
    
    # Zeige echte Datenwerte
    print(f"\n📋 Echte Datenbankwerte (Samples):")
    print(f"🏙️  Städte: {list(generator.real_cities)[:5]}")
    print(f"🏠 Adressen: {list(generator.real_addresses)[:3]}")
    print(f"👥 Namen: {list(generator.real_names)[:5]}")
    print(f"🏢 Firmen: {list(generator.real_companies)[:3]}")
    
    # Generiere und speichere Golden Set
    golden_set = generator.save_realistic_golden_set()
    
    print(f"\n✅ Realistic Golden Set erfolgreich erstellt!")
    print(f"   📝 {len(golden_set['queries'])} realistische Queries")
    print(f"   🎯 Basierend auf echten Datenbankwerten")
    print(f"   📊 Performance-validiert")

if __name__ == "__main__":
    main()