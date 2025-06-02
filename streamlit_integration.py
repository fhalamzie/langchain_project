"""
streamlit_integration.py - Integration der verbesserten Q&A-Funktionalität in die bestehende Streamlit-Anwendung

Diese Datei dient als Einstiegspunkt für die Streamlit-Anwendung und integriert sowohl die 
bestehende Funktionalität aus generate_yaml_ui.py als auch die neue erweiterte Q&A-Funktionalität.
"""

import os
import sys
import streamlit as st
import importlib.util
from pathlib import Path

# Konfiguration
APP_TITLE = "WINCASA - DB-Dokumentationsgenerator & Abfrage-Tool"
ORIGINAL_MODULE = "generate_yaml_ui"
ENHANCED_QA_AVAILABLE = True

def load_module(module_name, file_path):
    """
    Lädt ein Python-Modul dynamisch aus einer Datei.
    
    Args:
        module_name: Name des zu ladenden Moduls
        file_path: Pfad zur Python-Datei
        
    Returns:
        Das geladene Modul oder None bei Fehler
    """
    try:
        # Prüfe, ob die Datei existiert
        if not os.path.exists(file_path):
            print(f"FEHLER: Datei {file_path} existiert nicht.")
            return None
            
        # Lade das Modul
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            print(f"FEHLER: Konnte spec für {module_name} nicht erstellen.")
            return None
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"FEHLER beim Laden von {module_name}: {e}")
        return None

def main():
    """Hauptfunktion für die integrierte Streamlit-Anwendung."""
    # Konfiguriere die Streamlit-Seite
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Versuche, die erweiterte Q&A-Funktionalität zu laden
    try:
        # Lade qa_enhancer.py
        qa_enhancer_path = Path(__file__).parent / "qa_enhancer.py"
        qa_enhancer = load_module("qa_enhancer", qa_enhancer_path)
        
        # Lade enhanced_qa_ui.py
        enhanced_qa_ui_path = Path(__file__).parent / "enhanced_qa_ui.py"
        enhanced_qa_ui = load_module("enhanced_qa_ui", enhanced_qa_ui_path)
        
        ENHANCED_QA_AVAILABLE = (qa_enhancer is not None and enhanced_qa_ui is not None)
    except Exception as e:
        print(f"FEHLER beim Laden der Q&A-Module: {e}")
        ENHANCED_QA_AVAILABLE = False
    
    # Seitentitel
    st.title("📄 Automatisierte Dokumentation & Abfrage für Wincasa Datenbank")
    
    # Lade das ursprüngliche Modul
    original_module_path = Path(__file__).parent / f"{ORIGINAL_MODULE}.py"
    original_module = load_module(ORIGINAL_MODULE, original_module_path)
    
    if original_module is None:
        st.error(f"FEHLER: Konnte das Modul {ORIGINAL_MODULE} nicht laden.")
        return
    
    # Erstelle Tabs
    if ENHANCED_QA_AVAILABLE:
        tabs = st.tabs([
            "Phase 1: Initialdokumentation", 
            "Phase 2: Optimierung", 
            "Exporte & Weitere Aktionen", 
            "LLM Chat",
            "🔍 Erweiterte Datenbankabfrage"
        ])
    else:
        tabs = st.tabs([
            "Phase 1: Initialdokumentation", 
            "Phase 2: Optimierung", 
            "Exporte & Weitere Aktionen", 
            "LLM Chat"
        ])
    
    # Phase 1 Tab
    with tabs[0]:
        st.header("Phase 1 - Grundlegende Dokumentation erstellen")
        # Hier würde die originale Phase-1-Funktionalität aufgerufen
        st.info("Bitte verwenden Sie die ursprüngliche Anwendung für diese Funktionalität.")
    
    # Phase 2 Tab
    with tabs[1]:
        st.header("Phase 2 - Optimierung mit bestehendem Wissen")
        # Hier würde die originale Phase-2-Funktionalität aufgerufen
        st.info("Bitte verwenden Sie die ursprüngliche Anwendung für diese Funktionalität.")
    
    # Exporte Tab
    with tabs[2]:
        st.header("Export und Downloads")
        # Hier würde die originale Export-Funktionalität aufgerufen
        st.info("Bitte verwenden Sie die ursprüngliche Anwendung für diese Funktionalität.")
    
    # Chat Tab
    with tabs[3]:
        st.header("💬 Chat mit dem LLM")
        # Hier würde die originale Chat-Funktionalität aufgerufen
        st.info("Bitte verwenden Sie die ursprüngliche Anwendung für diese Funktionalität.")
    
    # Erweiterte Q&A Tab (falls verfügbar)
    if ENHANCED_QA_AVAILABLE and len(tabs) > 4:
        with tabs[4]:
            try:
                enhanced_qa_ui.create_enhanced_qa_tab()
            except Exception as e:
                st.error(f"Fehler beim Laden des erweiterten Q&A-Tabs: {e}")
                st.info("Bitte stellen Sie sicher, dass alle Abhängigkeiten korrekt installiert sind.")

if __name__ == "__main__":
    main()