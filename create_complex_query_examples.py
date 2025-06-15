#!/usr/bin/env python3
"""
T12.004: Create comprehensive complex query pattern examples
Advanced German property management scenarios for WINCASA system
"""

import json
from pathlib import Path
from datetime import datetime

def get_complex_query_examples():
    """Return comprehensive complex query examples for German property management"""
    
    return {
        # Multi-entity relationship queries
        "cross_entity_analysis": {
            "category": "Cross-Entity Analysis",
            "description": "Complex queries spanning multiple business entities",
            "examples": [
                {
                    "query": "Zeige mir alle WEG-Objekte von Fahim Halamzie mit Beiratsmitgliedern und aktuellen Beschlüssen aus 2024",
                    "intent": "Multi-entity governance analysis",
                    "entities": ["eigentuemer", "weg", "beirat", "beschluss"],
                    "complexity": "high",
                    "expected_joins": ["OBJEKTE", "EIGENTUEMER", "BEIRAETE", "BESCHLUESSE"],
                    "business_value": "Complete governance overview for WEG properties"
                },
                {
                    "query": "Welche Mieter von Susanne Wagner haben Mietschulden über 1000€ und wohnen in Objekten mit laufenden Instandhaltungsmaßnahmen?",
                    "intent": "Risk analysis across tenant payments and maintenance",
                    "entities": ["mieter", "eigentuemer", "mietschulden", "instandhaltung"],
                    "complexity": "high",
                    "expected_joins": ["BEWOHNER", "KONTEN", "BUCHUNG", "OBJEKTE"],
                    "business_value": "Identify high-risk tenant situations"
                },
                {
                    "query": "Analysiere alle Sozialwohnungen in München mit WBS-pflichtigen Mietern und deren Nebenkostenabrechnungen für 2023",
                    "intent": "Social housing compliance analysis",
                    "entities": ["sozialwohnung", "wbs", "nebenkosten", "location"],
                    "complexity": "high",
                    "expected_joins": ["WOHNUNG", "BEWOHNER", "KONTEN", "OBJEKTE"],
                    "business_value": "Ensure social housing compliance"
                }
            ]
        },
        
        # Financial analytics and reporting
        "financial_analytics": {
            "category": "Financial Analytics & KPIs",
            "description": "Complex financial analysis and performance metrics",
            "examples": [
                {
                    "query": "Berechne die Eigenkapitalrendite aller Objekte von Maria Huber und vergleiche mit Marktmieten in der Region",
                    "intent": "Investment performance analysis",
                    "entities": ["eigenkapitalrendite", "eigentuemer", "marktmiete"],
                    "complexity": "high",
                    "expected_calculations": ["ROE", "market_comparison", "performance_metrics"],
                    "business_value": "Investment performance optimization"
                },
                {
                    "query": "Zeige Cashflow-Entwicklung und Mietausfallrisiko für alle Objekte in Berlin mit Leerstandsquote über 10%",
                    "intent": "Risk-adjusted financial analysis",
                    "entities": ["cashflow", "mietausfall", "leerstand", "location"],
                    "complexity": "high",
                    "expected_calculations": ["cashflow_trend", "vacancy_impact", "risk_metrics"],
                    "business_value": "Proactive risk management"
                },
                {
                    "query": "Analysiere Betriebskosteneffizienz nach BetrKV für alle WEG-Objekte mit mehr als 20 Einheiten",
                    "intent": "Operating cost efficiency analysis",
                    "entities": ["betriebskosten", "betrkv", "weg", "einheiten"],
                    "complexity": "high",
                    "expected_calculations": ["cost_per_unit", "efficiency_ratios", "benchmark_comparison"],
                    "business_value": "Cost optimization and legal compliance"
                }
            ]
        },
        
        # Temporal and trend analysis
        "temporal_analysis": {
            "category": "Temporal & Trend Analysis",
            "description": "Time-based patterns and historical analysis",
            "examples": [
                {
                    "query": "Vergleiche Mietpreisentwicklung der letzten 5 Jahre mit Instandhaltungskosten für alle Objekte von Wolfgang Bauer",
                    "intent": "Long-term investment analysis",
                    "entities": ["mietpreisentwicklung", "instandhaltungskosten", "eigentuemer"],
                    "complexity": "high",
                    "temporal_scope": "5_years",
                    "business_value": "Strategic investment planning"
                },
                {
                    "query": "Identifiziere saisonale Leerstandsmuster und deren Auswirkung auf die Liquidität bei allen Münchener Objekten",
                    "intent": "Seasonal pattern analysis",
                    "entities": ["leerstand", "liquidität", "location"],
                    "complexity": "high",
                    "temporal_scope": "seasonal",
                    "business_value": "Seasonal planning and liquidity management"
                },
                {
                    "query": "Analysiere Mieterwechselhäufigkeit und Kündigungsmuster nach Wohnungsgröße und Mietpreiskategorie",
                    "intent": "Tenant turnover analysis",
                    "entities": ["mieterwechsel", "kündigung", "wohnungsgröße", "mietpreis"],
                    "complexity": "high",
                    "temporal_scope": "multi_year",
                    "business_value": "Tenant retention strategy"
                }
            ]
        },
        
        # Legal compliance and regulatory
        "legal_compliance": {
            "category": "Legal Compliance & Regulatory",
            "description": "German property law and regulatory compliance queries",
            "examples": [
                {
                    "query": "Prüfe Mietpreisbremse-Konformität für alle Neuvermietungen seit 2023 in angespannten Wohnungsmärkten",
                    "intent": "Rent cap compliance analysis",
                    "entities": ["mietpreisbremse", "neuvermietung", "angespannter_markt"],
                    "complexity": "high",
                    "legal_scope": "mietrecht",
                    "business_value": "Legal compliance assurance"
                },
                {
                    "query": "Analysiere WEG-Beschlussfähigkeit und Stimmenverteilung für alle anstehenden Modernisierungsbeschlüsse",
                    "intent": "WEG governance compliance",
                    "entities": ["weg", "beschlussfähigkeit", "modernisierung", "stimmenverteilung"],
                    "complexity": "high",
                    "legal_scope": "weg_recht",
                    "business_value": "Governance compliance and decision making"
                },
                {
                    "query": "Überprüfe Kündigungsschutz-Status aller Mieter mit Mietdauer über 5 Jahre und identifiziere erhöhte Schutzfristen",
                    "intent": "Tenant protection analysis",
                    "entities": ["kündigungsschutz", "mietdauer", "schutzfristen"],
                    "complexity": "high", 
                    "legal_scope": "mieterschutz",
                    "business_value": "Legal risk management"
                }
            ]
        },
        
        # Advanced portfolio optimization
        "portfolio_optimization": {
            "category": "Portfolio Optimization",
            "description": "Strategic portfolio management and optimization",
            "examples": [
                {
                    "query": "Identifiziere Objekte mit suboptimaler Flächennutzung und Potenzial für Grundrissoptimierung oder Teilung",
                    "intent": "Space utilization optimization",
                    "entities": ["flächennutzung", "grundriss", "optimierung"],
                    "complexity": "high",
                    "optimization_type": "space_efficiency",
                    "business_value": "Maximize rental income through space optimization"
                },
                {
                    "query": "Analysiere Diversifikationsgrad des Portfolios nach Objekttyp, Lage und Mieterstruktur für Risikostreuung",
                    "intent": "Portfolio risk diversification",
                    "entities": ["diversifikation", "objekttyp", "lage", "mieterstruktur"],
                    "complexity": "high",
                    "optimization_type": "risk_distribution",
                    "business_value": "Portfolio risk management"
                },
                {
                    "query": "Berechne optimale Instandhaltungsrücklage pro WEG basierend auf Gebäudealter, Zustand und geplanten Modernisierungen",
                    "intent": "Maintenance reserve optimization",
                    "entities": ["instandhaltungsrücklage", "weg", "gebäudealter", "modernisierung"],
                    "complexity": "high",
                    "optimization_type": "financial_planning",
                    "business_value": "Optimal financial planning"
                }
            ]
        },
        
        # Sustainability and ESG
        "sustainability_esg": {
            "category": "Sustainability & ESG",
            "description": "Environmental, social, and governance analysis",
            "examples": [
                {
                    "query": "Analysiere CO2-Fußabdruck und Energieeffizienz-Potential aller Objekte für EU-Taxonomie-Konformität",
                    "intent": "ESG compliance analysis",
                    "entities": ["co2_fußabdruck", "energieeffizienz", "eu_taxonomie"],
                    "complexity": "high",
                    "esg_scope": "environmental",
                    "business_value": "ESG compliance and sustainability reporting"
                },
                {
                    "query": "Bewerte soziale Nachhaltigkeit durch Mieterdemografie, Barrierefreiheit und Sozialwohnungsquote",
                    "intent": "Social sustainability assessment",
                    "entities": ["mieterdemografie", "barrierefreiheit", "sozialwohnung"],
                    "complexity": "high",
                    "esg_scope": "social",
                    "business_value": "Social impact measurement"
                },
                {
                    "query": "Identifiziere Objekte mit Smart-Home-Potential für Digitalisierung und Energieeinsparung",
                    "intent": "Technology integration analysis",
                    "entities": ["smart_home", "digitalisierung", "energieeinsparung"],
                    "complexity": "high",
                    "esg_scope": "technology",
                    "business_value": "Future-proofing and efficiency gains"
                }
            ]
        },
        
        # Predictive analytics scenarios
        "predictive_analytics": {
            "category": "Predictive Analytics",
            "description": "Forward-looking analysis and predictions",
            "examples": [
                {
                    "query": "Prognostiziere Leerstandsentwicklung basierend auf Markttrends, Objektzustand und lokaler Nachfrage",
                    "intent": "Vacancy prediction modeling",
                    "entities": ["leerstand", "markttrends", "objektzustand", "nachfrage"],
                    "complexity": "high",
                    "prediction_type": "vacancy_forecast",
                    "business_value": "Proactive vacancy management"
                },
                {
                    "query": "Schätze zukünftige Instandhaltungskosten basierend auf Gebäudealter, Nutzungsintensität und Wartungshistorie",
                    "intent": "Maintenance cost prediction",
                    "entities": ["instandhaltungskosten", "gebäudealter", "wartungshistorie"],
                    "complexity": "high",
                    "prediction_type": "cost_forecast",
                    "business_value": "Budget planning and financial forecasting"
                },
                {
                    "query": "Modelliere Mietpreisentwicklung unter verschiedenen Marktszenarien und regulatorischen Änderungen",
                    "intent": "Rent development scenario analysis",
                    "entities": ["mietpreisentwicklung", "marktszenarien", "regulatorisch"],
                    "complexity": "high",
                    "prediction_type": "scenario_modeling",
                    "business_value": "Strategic planning under uncertainty"
                }
            ]
        },
        
        # Integration with external data
        "external_integration": {
            "category": "External Data Integration",
            "description": "Queries incorporating external market and regulatory data",
            "examples": [
                {
                    "query": "Vergleiche Portfolio-Performance mit regionalen Immobilienindices und Benchmark-Portfolios",
                    "intent": "Benchmark comparison analysis",
                    "entities": ["portfolio_performance", "immobilienindex", "benchmark"],
                    "complexity": "high",
                    "external_data": ["market_indices", "benchmark_data"],
                    "business_value": "Competitive positioning analysis"
                },
                {
                    "query": "Integriere lokale Stadtentwicklungspläne für Bewertung von Standortpotenzial und Wertentwicklung",
                    "intent": "Urban development impact analysis",
                    "entities": ["stadtentwicklung", "standortpotenzial", "wertentwicklung"],
                    "complexity": "high",
                    "external_data": ["city_planning", "development_data"],
                    "business_value": "Location-based investment decisions"
                },
                {
                    "query": "Analysiere Auswirkungen neuer Gesetzgebung (z.B. WEG-Reform) auf Portfolio-Management und Compliance-Anforderungen",
                    "intent": "Regulatory impact analysis",
                    "entities": ["gesetzgebung", "weg_reform", "compliance"],
                    "complexity": "high",
                    "external_data": ["legal_updates", "regulatory_changes"],
                    "business_value": "Regulatory preparedness and compliance"
                }
            ]
        }
    }

def get_semantic_pattern_extensions():
    """Extended semantic patterns for complex queries"""
    
    return {
        "advanced_patterns": {
            "multi_entity_portfolio": {
                "name": "Multi-Entity Portfolio Analysis",
                "patterns": [
                    r"analysiere portfolio von (.+) mit (.+) und (.+)",
                    r"zeige (.+) für (.+) mit (.+) details",
                    r"vergleiche (.+) zwischen (.+) und (.+)"
                ],
                "parameters": ["entity1", "entity2", "entity3"],
                "complexity": "high",
                "description": "Complex analysis across multiple business entities"
            },
            "temporal_kpi_analysis": {
                "name": "Temporal KPI Analysis", 
                "patterns": [
                    r"entwicklung von (.+) über (.+) für (.+)",
                    r"trend (.+) letzten? (.+) bei (.+)",
                    r"vergleiche (.+) zwischen (.+) und (.+) zeitraum"
                ],
                "parameters": ["kpi", "timeframe", "entity"],
                "complexity": "high",
                "description": "Time-based KPI analysis and trends"
            },
            "compliance_analysis": {
                "name": "Compliance Analysis",
                "patterns": [
                    r"prüfe (.+) konformität für (.+)",
                    r"compliance (.+) nach (.+) für (.+)",
                    r"rechtliche prüfung (.+) bezüglich (.+)"
                ],
                "parameters": ["compliance_type", "regulation", "entity"],
                "complexity": "high",
                "description": "Legal and regulatory compliance analysis"
            },
            "predictive_modeling": {
                "name": "Predictive Modeling",
                "patterns": [
                    r"prognostiziere (.+) für (.+) basierend auf (.+)",
                    r"vorhersage (.+) unter (.+) bedingungen",
                    r"schätze (.+) entwicklung bei (.+)"
                ],
                "parameters": ["target_metric", "entity", "factors"],
                "complexity": "high",
                "description": "Predictive analysis and forecasting"
            },
            "optimization_analysis": {
                "name": "Optimization Analysis",
                "patterns": [
                    r"optimiere (.+) für (.+) unter (.+) constraints",
                    r"beste (.+) strategie für (.+)",
                    r"maximiere (.+) bei (.+) durch (.+)"
                ],
                "parameters": ["target", "entity", "constraints"],
                "complexity": "high", 
                "description": "Optimization and strategy analysis"
            }
        }
    }

def get_sql_template_examples():
    """Advanced SQL templates for complex patterns"""
    
    return {
        "advanced_templates": {
            "multi_entity_portfolio.sql": """
                WITH owner_portfolio AS (
                    SELECT e.*, o.ONR, o.OBEZ, o.OSTRASSE, o.OPLZORT
                    FROM EIGADR e
                    LEFT JOIN OBJEKTE o ON e.EIGNR = o.EIGNR
                    WHERE UPPER(e.ENAME) LIKE UPPER('%{entity1}%')
                ),
                tenant_details AS (
                    SELECT b.*, w.ENR, w.EFLAECHE, op.ONR, op.OBEZ
                    FROM BEWADR b
                    JOIN BEWOHNER bw ON b.BEWNR = bw.BEWNR  
                    JOIN WOHNUNG w ON bw.ENR = w.ENR
                    JOIN owner_portfolio op ON w.ONR = op.ONR
                ),
                financial_summary AS (
                    SELECT 
                        k.ONR,
                        SUM(CASE WHEN k.KKLASSE = 'MIETE' THEN k.KBRUTTO ELSE 0 END) as total_rent,
                        SUM(CASE WHEN k.KKLASSE = 'NK' THEN k.KBRUTTO ELSE 0 END) as total_operating_costs,
                        COUNT(DISTINCT td.BEWNR) as tenant_count
                    FROM KONTEN k
                    JOIN owner_portfolio op ON k.ONR = op.ONR
                    LEFT JOIN tenant_details td ON k.ONR = td.ONR
                    GROUP BY k.ONR
                )
                SELECT 
                    op.*,
                    td.BNAME, td.BVNAME, td.BSTR, td.BPLZORT,
                    fs.total_rent, fs.total_operating_costs, fs.tenant_count,
                    w.EFLAECHE, w.ETYP
                FROM owner_portfolio op
                LEFT JOIN tenant_details td ON op.ONR = td.ONR
                LEFT JOIN financial_summary fs ON op.ONR = fs.ONR
                LEFT JOIN WOHNUNG w ON op.ONR = w.ONR
                ORDER BY op.ENAME, op.OBEZ, td.BNAME
            """,
            
            "temporal_kpi_analysis.sql": """
                WITH monthly_metrics AS (
                    SELECT 
                        DATE_FORMAT(b.DATUM, '%Y-%m') as month_year,
                        k.ONR,
                        SUM(CASE WHEN k.KKLASSE = 'MIETE' THEN b.BETRAG ELSE 0 END) as monthly_rent,
                        SUM(CASE WHEN k.KKLASSE = 'NK' THEN b.BETRAG ELSE 0 END) as monthly_costs,
                        COUNT(DISTINCT b.BNR) as transaction_count
                    FROM BUCHUNG b
                    JOIN KONTEN k ON b.KNR = k.KNR
                    WHERE b.DATUM >= DATE_SUB(CURRENT_DATE, INTERVAL {timeframe} MONTH)
                    GROUP BY DATE_FORMAT(b.DATUM, '%Y-%m'), k.ONR
                ),
                trend_analysis AS (
                    SELECT 
                        mm.*,
                        LAG(mm.monthly_rent) OVER (PARTITION BY mm.ONR ORDER BY mm.month_year) as prev_rent,
                        LAG(mm.monthly_costs) OVER (PARTITION BY mm.ONR ORDER BY mm.month_year) as prev_costs
                    FROM monthly_metrics mm
                ),
                owner_objects AS (
                    SELECT o.ONR, o.OBEZ, e.ENAME
                    FROM OBJEKTE o
                    JOIN EIGADR e ON o.EIGNR = e.EIGNR
                    WHERE UPPER(e.ENAME) LIKE UPPER('%{entity}%')
                )
                SELECT 
                    ta.*,
                    oo.OBEZ, oo.ENAME,
                    ROUND((ta.monthly_rent - ta.prev_rent) / ta.prev_rent * 100, 2) as rent_change_percent,
                    ROUND((ta.monthly_costs - ta.prev_costs) / ta.prev_costs * 100, 2) as cost_change_percent
                FROM trend_analysis ta
                JOIN owner_objects oo ON ta.ONR = oo.ONR
                WHERE ta.prev_rent IS NOT NULL
                ORDER BY ta.month_year DESC, oo.ENAME, oo.OBEZ
            """,
            
            "compliance_analysis.sql": """
                WITH compliance_checks AS (
                    SELECT 
                        o.ONR, o.OBEZ, e.ENAME,
                        CASE 
                            WHEN '{compliance_type}' = 'MIETPREISBREMSE' THEN
                                CASE WHEN bw.Z1 <= (markt.MARKTMIETE * 1.1) THEN 'KONFORM' ELSE 'VERLETZUNG' END
                            WHEN '{compliance_type}' = 'BETRKV' THEN  
                                CASE WHEN k.KKLASSE IN ('NK', 'HEIZUNG', 'WASSER') THEN 'KONFORM' ELSE 'PRÜFUNG' END
                            WHEN '{compliance_type}' = 'WEG_BESCHLUSSFÄHIGKEIT' THEN
                                CASE WHEN weg.STIMMENVERHÄLTNIS >= 0.5 THEN 'BESCHLUSSFÄHIG' ELSE 'NICHT_BESCHLUSSFÄHIG' END
                            ELSE 'UNBEKANNT'
                        END as compliance_status,
                        bw.Z1 as current_rent,
                        markt.MARKTMIETE as market_rent,
                        k.KKLASSE as cost_category
                    FROM OBJEKTE o
                    JOIN EIGADR e ON o.EIGNR = e.EIGNR
                    LEFT JOIN WOHNUNG w ON o.ONR = w.ONR
                    LEFT JOIN BEWOHNER bw ON w.ENR = bw.ENR
                    LEFT JOIN KONTEN k ON o.ONR = k.ONR
                    LEFT JOIN (
                        SELECT ONR, AVG(MARKTMIETE_PRO_QM * WOHNFLÄCHE) as MARKTMIETE
                        FROM MARKTDATEN 
                        GROUP BY ONR
                    ) markt ON o.ONR = markt.ONR
                    LEFT JOIN (
                        SELECT ONR, 
                               SUM(STIMMANTEILE_ANWESEND) / SUM(STIMMANTEILE_GESAMT) as STIMMENVERHÄLTNIS
                        FROM WEG_VERSAMMLUNGEN
                        GROUP BY ONR
                    ) weg ON o.ONR = weg.ONR
                    WHERE UPPER(e.ENAME) LIKE UPPER('%{entity}%')
                ),
                violation_summary AS (
                    SELECT 
                        ONR, OBEZ, ENAME,
                        COUNT(*) as total_checks,
                        SUM(CASE WHEN compliance_status LIKE '%VERLETZUNG%' OR compliance_status LIKE '%NICHT_%' THEN 1 ELSE 0 END) as violations,
                        GROUP_CONCAT(DISTINCT compliance_status) as status_summary
                    FROM compliance_checks
                    GROUP BY ONR, OBEZ, ENAME
                )
                SELECT 
                    vs.*,
                    ROUND(vs.violations * 100.0 / vs.total_checks, 2) as violation_percentage,
                    CASE 
                        WHEN vs.violations = 0 THEN 'VOLLSTÄNDIG_KONFORM'
                        WHEN vs.violations <= vs.total_checks * 0.1 THEN 'GERINGFÜGIGE_MÄNGEL'
                        ELSE 'ERHEBLICHE_MÄNGEL'
                    END as overall_compliance
                FROM violation_summary vs
                ORDER BY vs.violation_percentage DESC, vs.ENAME
            """
        }
    }

def main():
    knowledge_base_path = "data/knowledge_base"
    
    # Create directory if it doesn't exist
    Path(knowledge_base_path).mkdir(parents=True, exist_ok=True)
    
    print("🔄 Creating comprehensive complex query pattern examples...")
    
    # Generate complex query examples
    complex_examples = get_complex_query_examples()
    semantic_extensions = get_semantic_pattern_extensions()
    sql_templates = get_sql_template_examples()
    
    # Save complex query examples
    examples_file = Path(knowledge_base_path) / "complex_query_examples.json"
    with open(examples_file, 'w', encoding='utf-8') as f:
        json.dump(complex_examples, f, ensure_ascii=False, indent=2)
    
    # Save semantic pattern extensions
    patterns_file = Path(knowledge_base_path) / "semantic_pattern_extensions.json" 
    with open(patterns_file, 'w', encoding='utf-8') as f:
        json.dump(semantic_extensions, f, ensure_ascii=False, indent=2)
    
    # Save advanced SQL templates
    templates_file = Path(knowledge_base_path) / "advanced_sql_templates.json"
    with open(templates_file, 'w', encoding='utf-8') as f:
        json.dump(sql_templates, f, ensure_ascii=False, indent=2)
    
    # Count examples
    total_examples = sum(len(category["examples"]) for category in complex_examples.values())
    total_patterns = len(semantic_extensions["advanced_patterns"])
    total_templates = len(sql_templates["advanced_templates"])
    
    print(f"📊 Complex Query Examples Created:")
    print(f"   • Query Examples: {total_examples} across {len(complex_examples)} categories")
    print(f"   • Semantic Patterns: {total_patterns} advanced patterns")
    print(f"   • SQL Templates: {total_templates} complex templates")
    
    print(f"\n📋 Categories Covered:")
    for category_key, category_data in complex_examples.items():
        example_count = len(category_data["examples"])
        print(f"   • {category_data['category']}: {example_count} examples")
    
    print(f"\n📝 Files Created:")
    print(f"   • {examples_file}")
    print(f"   • {patterns_file}")
    print(f"   • {templates_file}")
    
    print(f"\n✅ T12.004 COMPLETED: Complex query pattern examples created")
    print(f"🎯 Quality Focus: Advanced German property management scenarios covered")

if __name__ == "__main__":
    main()