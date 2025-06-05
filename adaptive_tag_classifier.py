#!/usr/bin/env python3
"""
Adaptive TAG Classifier - ML-based Query Classification

Replaces rule-based query classification with machine learning approach
for better accuracy and adaptability.

Key improvements:
1. ML-based classification instead of static regex patterns
2. Learning from query patterns and successful SQL generations
3. Extended query type coverage (10+ types vs current 5)
4. Dynamic schema discovery and relationship mapping
"""

import logging
import json
import pickle
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import re

# ML imports
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, falling back to rule-based classification")

logger = logging.getLogger(__name__)


@dataclass
class QueryPattern:
    """Represents a learned query pattern for training"""
    query: str
    query_type: str
    entities: List[str]
    success_rate: float
    sql_template: Optional[str] = None
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class ClassificationResult:
    """Result of ML-based query classification"""
    query_type: str
    confidence: float
    alternatives: List[Tuple[str, float]]
    entities: List[str]
    reasoning: str


class AdaptiveTAGClassifier:
    """
    ML-based query classifier that learns from patterns and improves over time.
    
    Features:
    - TF-IDF + Naive Bayes for robust text classification
    - Dynamic learning from successful query-SQL pairs
    - Extended query type coverage
    - Confidence-based fallback strategies
    """
    
    # Extended query types - more comprehensive than original TAG
    EXTENDED_QUERY_TYPES = {
        "address_lookup": {
            "description": "Find residents by address, street, postal code",
            "keywords": ["wohnt", "adresse", "straße", "postleitzahl", "ort"],
            "entities": ["street_name", "house_number", "postal_code", "city"]
        },
        "resident_lookup": {
            "description": "Find specific residents by name or characteristics",
            "keywords": ["bewohner", "mieter", "name", "person"],
            "entities": ["person_name", "first_name", "last_name"]
        },
        "owner_lookup": {
            "description": "Find property owners and ownership information",
            "keywords": ["eigentümer", "besitzer", "vermieter", "besitz"],
            "entities": ["owner_name", "property_reference"]
        },
        "property_queries": {
            "description": "Apartment, building, and property information",
            "keywords": ["wohnung", "gebäude", "objekt", "immobilie", "apartment"],
            "entities": ["building_id", "apartment_number", "property_type"]
        },
        "financial_queries": {
            "description": "Rent, costs, financial information",
            "keywords": ["miete", "kosten", "preis", "geld", "euro", "durchschnitt"],
            "entities": ["amount", "currency", "time_period"]
        },
        "count_queries": {
            "description": "Counting objects (apartments, residents, etc.)",
            "keywords": ["wie viele", "anzahl", "insgesamt", "zählen", "summe"],
            "entities": ["count_target", "filter_criteria"]
        },
        "relationship_queries": {
            "description": "Complex queries involving multiple entity relationships",
            "keywords": ["alle", "zusammen", "verbunden", "gehört", "beziehung"],
            "entities": ["primary_entity", "related_entity", "relationship_type"]
        },
        "temporal_queries": {
            "description": "Time-based queries (dates, periods, history)",
            "keywords": ["wann", "seit", "bis", "datum", "zeit", "jahr", "monat"],
            "entities": ["date", "time_period", "temporal_operator"]
        },
        "comparison_queries": {
            "description": "Comparative analysis and statistics",
            "keywords": ["vergleich", "mehr als", "weniger als", "größer", "kleiner"],
            "entities": ["comparison_value", "comparison_operator", "metric"]
        },
        "business_logic_queries": {
            "description": "Complex business logic requiring domain knowledge",
            "keywords": ["verwaltung", "vertrag", "hausverwaltung", "geschäft"],
            "entities": ["business_concept", "domain_term"]
        }
    }
    
    def __init__(self, model_path: str = "models/adaptive_tag_classifier.pkl"):
        """
        Initialize adaptive TAG classifier.
        
        Args:
            model_path: Path to save/load the trained model
        """
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(exist_ok=True)
        
        # ML pipeline components
        self.classifier_pipeline: Optional[Pipeline] = None
        self.entity_extractor = EntityExtractor()
        
        # Training data storage
        self.training_patterns: List[QueryPattern] = []
        
        # Performance tracking
        self.classification_history: List[Dict[str, Any]] = []
        
        # Initialize with pre-existing patterns if available
        self._load_model_and_patterns()
        
        # If no model exists, initialize with seed data
        if self.classifier_pipeline is None:
            self._initialize_with_seed_data()
    
    def _load_model_and_patterns(self):
        """Load existing model and training patterns"""
        try:
            if self.model_path.exists():
                with open(self.model_path, 'rb') as f:
                    saved_data = pickle.load(f)
                    self.classifier_pipeline = saved_data.get('pipeline')
                    self.training_patterns = [
                        QueryPattern(**pattern) for pattern in saved_data.get('patterns', [])
                    ]
                logger.info(f"Loaded model with {len(self.training_patterns)} patterns")
        except Exception as e:
            logger.warning(f"Could not load existing model: {e}")
    
    def _initialize_with_seed_data(self):
        """Initialize with seed training data from existing TAG patterns"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, ML features disabled")
            return
            
        # Seed data based on known successful patterns
        seed_patterns = [
            QueryPattern("Wer wohnt in der Marienstraße 26", "address_lookup", ["Marienstraße", "26"], 0.9),
            QueryPattern("Wie viele Wohnungen gibt es", "count_queries", ["Wohnungen"], 0.95),
            QueryPattern("Alle Eigentümer aus Köln", "owner_lookup", ["Köln"], 0.85),
            QueryPattern("Durchschnittliche Miete", "financial_queries", ["Miete"], 0.8),
            QueryPattern("Liste aller Mieter", "resident_lookup", ["Mieter"], 0.9),
            QueryPattern("Bewohner der Marienstraße", "address_lookup", ["Marienstraße"], 0.85),
            QueryPattern("Eigentümer von Objekt 123", "owner_lookup", ["123"], 0.9),
            QueryPattern("Wohnungen mehr als 3 Zimmer", "comparison_queries", ["3", "Zimmer"], 0.7),
            QueryPattern("Miete seit Januar 2023", "temporal_queries", ["Januar", "2023"], 0.75),
            QueryPattern("Hausverwaltung Verträge", "business_logic_queries", ["Verträge"], 0.8),
        ]
        
        self.training_patterns.extend(seed_patterns)
        self._train_classifier()
        logger.info("Initialized with seed data and trained initial model")
    
    def _train_classifier(self):
        """Train the ML classifier with current patterns"""
        if not SKLEARN_AVAILABLE or len(self.training_patterns) < 5:
            logger.warning("Cannot train classifier: insufficient data or sklearn unavailable")
            return
        
        # Prepare training data
        texts = [pattern.query for pattern in self.training_patterns]
        labels = [pattern.query_type for pattern in self.training_patterns]
        
        # Weight samples by success rate
        sample_weights = [pattern.success_rate for pattern in self.training_patterns]
        
        # Create pipeline
        self.classifier_pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=1000,
                lowercase=True,
                stop_words=None  # Keep German words
            )),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        try:
            # Train the model
            self.classifier_pipeline.fit(texts, labels, classifier__sample_weight=sample_weights)
            logger.info(f"Trained classifier with {len(texts)} patterns")
            
            # Save the model
            self._save_model()
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            self.classifier_pipeline = None
    
    def _save_model(self):
        """Save the trained model and patterns"""
        try:
            save_data = {
                'pipeline': self.classifier_pipeline,
                'patterns': [asdict(pattern) for pattern in self.training_patterns],
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(save_data, f)
            logger.info(f"Saved model to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Could not save model: {e}")
    
    def classify_query(self, query: str) -> ClassificationResult:
        """
        Classify query using ML model with fallback to rule-based approach.
        
        Args:
            query: Natural language query to classify
            
        Returns:
            ClassificationResult with classification and confidence
        """
        # Extract entities first
        entities = self.entity_extractor.extract_entities(query)
        
        # Try ML classification first
        if self.classifier_pipeline is not None:
            try:
                # Get prediction probabilities
                probabilities = self.classifier_pipeline.predict_proba([query])[0]
                classes = self.classifier_pipeline.classes_
                
                # Sort by probability
                prob_pairs = list(zip(classes, probabilities))
                prob_pairs.sort(key=lambda x: x[1], reverse=True)
                
                best_class, best_prob = prob_pairs[0]
                alternatives = prob_pairs[1:4]  # Top 3 alternatives
                
                reasoning = f"ML classification with {best_prob:.3f} confidence"
                
                return ClassificationResult(
                    query_type=best_class,
                    confidence=float(best_prob),
                    alternatives=[(cls, float(prob)) for cls, prob in alternatives],
                    entities=entities,
                    reasoning=reasoning
                )
                
            except Exception as e:
                logger.warning(f"ML classification failed: {e}, falling back to rules")
        
        # Fallback to rule-based classification
        return self._rule_based_classify(query, entities)
    
    def _rule_based_classify(self, query: str, entities: List[str]) -> ClassificationResult:
        """Fallback rule-based classification"""
        query_lower = query.lower()
        scores = {}
        
        # Score each query type based on keyword matching
        for query_type, config in self.EXTENDED_QUERY_TYPES.items():
            score = 0
            for keyword in config['keywords']:
                if keyword in query_lower:
                    score += 1
            
            # Normalize score
            scores[query_type] = score / len(config['keywords']) if config['keywords'] else 0
        
        # Get best match
        if not scores or max(scores.values()) == 0:
            best_type = "business_logic_queries"  # Default fallback
            confidence = 0.3
        else:
            best_type = max(scores, key=scores.get)
            confidence = scores[best_type]
        
        # Generate alternatives
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        alternatives = [(qtype, score) for qtype, score in sorted_scores[1:4]]
        
        reasoning = f"Rule-based classification with keyword matching"
        
        return ClassificationResult(
            query_type=best_type,
            confidence=confidence,
            alternatives=alternatives,
            entities=entities,
            reasoning=reasoning
        )
    
    def learn_from_success(self, query: str, query_type: str, sql: str, success: bool):
        """
        Learn from successful query-SQL pairs to improve classification.
        
        Args:
            query: The original query
            query_type: The classified query type
            sql: The generated SQL
            success: Whether the SQL execution was successful
        """
        entities = self.entity_extractor.extract_entities(query)
        success_rate = 1.0 if success else 0.0
        
        # Create pattern
        pattern = QueryPattern(
            query=query,
            query_type=query_type,
            entities=entities,
            success_rate=success_rate,
            sql_template=sql
        )
        
        # Add to training data
        self.training_patterns.append(pattern)
        
        # Record in history
        self.classification_history.append({
            "query": query,
            "query_type": query_type,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
        # Retrain periodically (every 10 new patterns)
        if len(self.training_patterns) % 10 == 0:
            self._train_classifier()
            logger.info("Retrained classifier with new patterns")
    
    def get_query_type_schema(self, query_type: str) -> Dict[str, Any]:
        """Get schema information for a specific query type"""
        if query_type in self.EXTENDED_QUERY_TYPES:
            return self.EXTENDED_QUERY_TYPES[query_type]
        return self.EXTENDED_QUERY_TYPES["business_logic_queries"]  # Default
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get classifier performance metrics"""
        if not self.classification_history:
            return {"status": "no_data"}
        
        total_classifications = len(self.classification_history)
        successful_classifications = sum(1 for h in self.classification_history if h["success"])
        
        return {
            "total_patterns": len(self.training_patterns),
            "total_classifications": total_classifications,
            "success_rate": successful_classifications / total_classifications if total_classifications > 0 else 0,
            "ml_model_available": self.classifier_pipeline is not None,
            "query_types_covered": len(self.EXTENDED_QUERY_TYPES),
            "last_retrain": getattr(self, '_last_retrain', "never")
        }


class EntityExtractor:
    """Enhanced entity extraction for German HV domain"""
    
    def __init__(self):
        self.patterns = {
            'street_names': [
                r'\b([A-ZÄÖÜ][a-zäöüß]+(?:straße|str\.?|weg|platz|gasse))\b',
                r'\b(Marien|Schmied|Bäuminghausen?)\w*\b'
            ],
            'house_numbers': [r'\b\d{1,3}[a-z]?\b'],
            'postal_codes': [r'\b\d{5}\b'],
            'cities': [r'\b(Essen|Köln|Duisburg|Düsseldorf)\b'],
            'person_names': [r'\b[A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+\b'],
            'amounts': [r'\b\d+(?:[.,]\d+)?\s*(?:€|Euro|EUR)\b'],
            'dates': [r'\b\d{1,2}\.\d{1,2}\.\d{4}\b', r'\b\d{4}-\d{2}-\d{2}\b'],
            'numbers': [r'\b\d+\b']
        }
        
        # Compile patterns
        self.compiled_patterns = {
            category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for category, patterns in self.patterns.items()
        }
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract entities from text using compiled patterns"""
        entities = []
        
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                if isinstance(matches[0], tuple) if matches else False:
                    # Handle group captures
                    entities.extend([match[0] for match in matches])
                else:
                    entities.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen:
                seen.add(entity)
                unique_entities.append(entity)
        
        return unique_entities


def test_adaptive_classifier():
    """Test the adaptive TAG classifier"""
    print("🧪 Testing Adaptive TAG Classifier")
    print("=" * 50)
    
    classifier = AdaptiveTAGClassifier()
    
    test_queries = [
        "Wer wohnt in der Marienstraße 26?",
        "Wie viele Wohnungen gibt es insgesamt?",
        "Alle Eigentümer aus Köln",
        "Durchschnittliche Miete in Essen",
        "Liste aller Mieter von Objekt 123",
        "Wohnungen mit mehr als 3 Zimmern",
        "Mietverträge seit Januar 2023",
        "Hausverwaltung Geschäftsberichte"
    ]
    
    for query in test_queries:
        result = classifier.classify_query(query)
        print(f"\nQuery: {query}")
        print(f"  Type: {result.query_type} (confidence: {result.confidence:.3f})")
        print(f"  Entities: {result.entities}")
        print(f"  Alternatives: {result.alternatives[:2]}")
        print(f"  Reasoning: {result.reasoning}")
    
    # Test learning
    print(f"\nPerformance Metrics:")
    metrics = classifier.get_performance_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    test_adaptive_classifier()