#!/usr/bin/env python3
"""
WINCASA Production Configuration
Centralized configuration management for production deployment.
"""

import os
from pathlib import Path
from typing import Dict, Any, List
import logging

class ProductionConfig:
    """Production configuration settings for WINCASA system."""
    
    # Project structure
    PROJECT_ROOT = Path(__file__).parent.absolute()
    
    # Database configuration
    DATABASE_PATH = PROJECT_ROOT / "WINCASA2022.FDB"
    FB_CLIENT_LIB = PROJECT_ROOT / "lib" / "libfbclient.so"
    FB_TEMP_DIR = PROJECT_ROOT / "fb_temp_direct"
    
    # API configuration
    OPENAI_ENV_PATH = Path("/home/envs/openai.env")
    OPENROUTER_ENV_PATH = Path("/home/envs/openrouter.env")
    
    # Documentation and knowledge base
    OUTPUT_DIR = PROJECT_ROOT / "output"
    YAML_DOCS_DIR = OUTPUT_DIR / "yamls"
    SCHEMA_DOCS_DIR = OUTPUT_DIR / "schema"
    KNOWLEDGE_BASE_PATH = OUTPUT_DIR / "compiled_knowledge_base.json"
    
    # Streamlit configuration
    STREAMLIT_PORT = 8501
    STREAMLIT_HOST = "0.0.0.0"  # For production access
    
    # Performance settings
    MAX_QUERY_TIMEOUT = 30  # seconds
    MAX_RESULT_ROWS = 1000
    DOCUMENT_CONTENT_LIMIT = 1500  # characters
    MAX_RETRIEVAL_DOCS = 15
    
    # Security settings
    ALLOWED_SQL_OPERATIONS = ["SELECT"]
    ENABLE_SQL_VALIDATION = True
    ENABLE_QUERY_LOGGING = True
    
    # Monitoring and logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR = PROJECT_ROOT / "logs"
    
    @classmethod
    def setup_production_environment(cls) -> Dict[str, Any]:
        """Setup production environment and validate configuration."""
        config = {}
        
        # Create necessary directories
        cls._ensure_directories()
        
        # Setup logging
        cls._setup_logging()
        
        # Validate critical files
        validation_result = cls._validate_environment()
        config['validation'] = validation_result
        
        # Load API keys
        config['api_keys'] = cls._load_api_keys()
        
        # Database configuration
        config['database'] = {
            'path': str(cls.DATABASE_PATH),
            'client_lib': str(cls.FB_CLIENT_LIB),
            'temp_dir': str(cls.FB_TEMP_DIR),
            'connection_string': f"firebird+fdb://sysdba:masterkey@/{cls.DATABASE_PATH}"
        }
        
        # Streamlit configuration
        config['streamlit'] = {
            'port': cls.STREAMLIT_PORT,
            'host': cls.STREAMLIT_HOST,
            'command': f"streamlit run enhanced_qa_ui.py --server.port {cls.STREAMLIT_PORT} --server.address {cls.STREAMLIT_HOST}"
        }
        
        # Performance settings
        config['performance'] = {
            'query_timeout': cls.MAX_QUERY_TIMEOUT,
            'max_result_rows': cls.MAX_RESULT_ROWS,
            'document_limit': cls.DOCUMENT_CONTENT_LIMIT,
            'max_retrieval_docs': cls.MAX_RETRIEVAL_DOCS
        }
        
        return config
    
    @classmethod
    def _ensure_directories(cls):
        """Create necessary directories for production."""
        directories = [
            cls.OUTPUT_DIR,
            cls.YAML_DOCS_DIR,
            cls.SCHEMA_DOCS_DIR,
            cls.FB_TEMP_DIR,
            cls.LOG_DIR,
            cls.PROJECT_ROOT / "output" / "logs",
            cls.PROJECT_ROOT / "output" / "memory",
            cls.PROJECT_ROOT / "output" / "feedback",
            cls.PROJECT_ROOT / "output" / "cache"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def _setup_logging(cls):
        """Setup production logging configuration."""
        log_file = cls.LOG_DIR / "wincasa_production.log"
        
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format=cls.LOG_FORMAT,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        # Set third-party library log levels
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('openai').setLevel(logging.WARNING)
        logging.getLogger('langchain').setLevel(logging.WARNING)
    
    @classmethod
    def _validate_environment(cls) -> Dict[str, bool]:
        """Validate production environment requirements."""
        validation = {}
        
        # Check database file
        validation['database_exists'] = cls.DATABASE_PATH.exists()
        
        # Check Firebird client library
        validation['fb_client_exists'] = cls.FB_CLIENT_LIB.exists()
        
        # Check API key files
        validation['openai_env_exists'] = cls.OPENAI_ENV_PATH.exists()
        validation['openrouter_env_exists'] = cls.OPENROUTER_ENV_PATH.exists()
        
        # Check documentation
        validation['yaml_docs_exist'] = cls.YAML_DOCS_DIR.exists() and len(list(cls.YAML_DOCS_DIR.glob("*.yaml"))) > 0
        validation['schema_docs_exist'] = cls.SCHEMA_DOCS_DIR.exists()
        
        # Check Python environment
        validation['virtual_env_active'] = (
            hasattr(os, 'real_prefix') or 
            (hasattr(os, 'base_prefix') and os.base_prefix != os.prefix) or
            'VIRTUAL_ENV' in os.environ
        )
        
        return validation
    
    @classmethod
    def _load_api_keys(cls) -> Dict[str, bool]:
        """Load and validate API keys."""
        api_keys = {}
        
        # OpenAI API key
        if cls.OPENAI_ENV_PATH.exists():
            try:
                with open(cls.OPENAI_ENV_PATH, 'r') as f:
                    content = f.read().strip()
                    api_keys['openai_configured'] = 'OPENAI_API_KEY=' in content and len(content.split('=')[1]) > 10
            except Exception:
                api_keys['openai_configured'] = False
        else:
            api_keys['openai_configured'] = False
        
        # OpenRouter API key (optional fallback)
        if cls.OPENROUTER_ENV_PATH.exists():
            try:
                with open(cls.OPENROUTER_ENV_PATH, 'r') as f:
                    content = f.read().strip()
                    api_keys['openrouter_configured'] = 'OPENROUTER_API_KEY=' in content and len(content.split('=')[1]) > 10
            except Exception:
                api_keys['openrouter_configured'] = False
        else:
            api_keys['openrouter_configured'] = False
        
        return api_keys
    
    @classmethod
    def get_production_status(cls) -> Dict[str, Any]:
        """Get current production readiness status."""
        config = cls.setup_production_environment()
        
        # Overall readiness assessment
        validation = config['validation']
        api_keys = config['api_keys']
        
        critical_requirements = [
            validation.get('database_exists', False),
            validation.get('fb_client_exists', False),
            api_keys.get('openai_configured', False),
            validation.get('yaml_docs_exist', False),
            validation.get('virtual_env_active', False)
        ]
        
        production_ready = all(critical_requirements)
        
        status = {
            'production_ready': production_ready,
            'critical_requirements_met': sum(critical_requirements),
            'total_requirements': len(critical_requirements),
            'validation_details': validation,
            'api_configuration': api_keys,
            'recommendations': cls._get_recommendations(validation, api_keys)
        }
        
        return status
    
    @classmethod
    def _get_recommendations(cls, validation: Dict[str, bool], api_keys: Dict[str, bool]) -> List[str]:
        """Get recommendations for production deployment."""
        recommendations = []
        
        if not validation.get('database_exists', False):
            recommendations.append("❌ Database file WINCASA2022.FDB not found in project root")
        
        if not validation.get('fb_client_exists', False):
            recommendations.append("❌ Firebird client library not found at ./lib/libfbclient.so")
        
        if not api_keys.get('openai_configured', False):
            recommendations.append("❌ OpenAI API key not configured in /home/envs/openai.env")
        
        if not validation.get('yaml_docs_exist', False):
            recommendations.append("❌ YAML documentation not found in output/yamls/")
        
        if not validation.get('virtual_env_active', False):
            recommendations.append("❌ Python virtual environment not activated")
        
        if not recommendations:
            recommendations.append("✅ All production requirements met - system ready for deployment")
        
        return recommendations


if __name__ == "__main__":
    """Production configuration validation."""
    print("🚀 WINCASA Production Configuration Validator")
    print("=" * 50)
    
    config = ProductionConfig()
    status = config.get_production_status()
    
    print(f"Production Ready: {'✅ YES' if status['production_ready'] else '❌ NO'}")
    print(f"Requirements Met: {status['critical_requirements_met']}/{status['total_requirements']}")
    print()
    
    print("📋 Recommendations:")
    for rec in status['recommendations']:
        print(f"  {rec}")
    
    print()
    print("🔧 Validation Details:")
    for key, value in status['validation_details'].items():
        status_icon = "✅" if value else "❌"
        print(f"  {status_icon} {key}: {value}")
    
    print()
    print("🔑 API Configuration:")
    for key, value in status['api_configuration'].items():
        status_icon = "✅" if value else "❌"
        print(f"  {status_icon} {key}: {value}")