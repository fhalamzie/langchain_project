#!/usr/bin/env python3
"""
WINCASA Layer 2 Configuration Loader
Zentrale Konfiguration für alle Modi aus .env Datei
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


class WincasaConfig:
    """Zentrale Konfigurationsklasse für alle WINCASA Layer 2 Modi"""
    
    def __init__(self, env_file=None):
        """
        Initialisiert Konfiguration aus .env Datei
        
        Args:
            env_file: Pfad zur .env Datei (optional)
        """
        if env_file is None:
            env_file = Path(__file__).parent.parent.parent.parent / 'config' / '.env'
        
        # Lade .env Datei
        load_dotenv(env_file)
        
        # Lade API Keys aus separater Datei
        self._load_api_keys()
        
        self._config = self._load_config()
        self._setup_logging()
    
    def _load_api_keys(self):
        """Lädt API Keys aus separaten .env Dateien (OpenAI only)"""
        # Prüfe ob bereits geladen
        if hasattr(self, '_api_keys_loaded'):
            return
        
        # Load OpenAI API keys
        openai_keys_file = os.getenv('OPENAI_API_KEYS_FILE', '/home/envs/openai.env')
        if os.path.exists(openai_keys_file):
            load_dotenv(openai_keys_file, override=True)
            print(f"OpenAI API Keys geladen aus: {openai_keys_file}")
        
        self._api_keys_loaded = True
    
    def _load_config(self) -> Dict[str, Any]:
        """Lädt alle Konfigurationswerte aus Umgebungsvariablen"""
        return {
            # LLM Configuration - OpenAI Only
            'llm_provider': 'openai',
            
            # OpenAI Configuration
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'openai_model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            'openai_temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.1')),
            'openai_max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '4000')),
            
            # System Mode
            'system_mode': os.getenv('SYSTEM_MODE', 'json_standard'),
            
            # Database Configuration
            'db_path': os.getenv('DB_PATH', '/home/projects/wincasa_llm/data/wincasa_data/WINCASA2022.FDB'),
            'db_user': os.getenv('DB_USER', 'SYSDBA'),
            'db_password': os.getenv('DB_PASSWORD', 'masterkey'),
            'db_charset': os.getenv('DB_CHARSET', 'ISO8859_1'),
            
            # Export Configuration
            'json_export_dir': os.getenv('JSON_EXPORT_DIR', './json_exports'),
            'json_auto_export': os.getenv('JSON_AUTO_EXPORT', 'true').lower() == 'true',
            
            # Scheduler Configuration
            'scheduler_enabled': os.getenv('SCHEDULER_ENABLED', 'true').lower() == 'true',
            'scheduler_interval': os.getenv('SCHEDULER_INTERVAL', 'daily'),
            'scheduler_time': os.getenv('SCHEDULER_TIME', '06:00'),
            'scheduler_timezone': os.getenv('SCHEDULER_TIMEZONE', 'Europe/Berlin'),
            'scheduler_max_retries': int(os.getenv('SCHEDULER_MAX_RETRIES', '3')),
            'scheduler_cleanup_days': int(os.getenv('SCHEDULER_CLEANUP_DAYS', '30')),
            
            # Testing Configuration
            'ab_testing_enabled': os.getenv('AB_TESTING_ENABLED', 'false').lower() == 'true',
            'ab_test_sample_size': int(os.getenv('AB_TEST_SAMPLE_SIZE', '10')),
            'ab_test_metrics': os.getenv('AB_TEST_METRICS', 'accuracy,speed,user_satisfaction').split(','),
            
            # Logging
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_file': os.getenv('LOG_FILE', './layer2.log'),
            
            # Performance
            'performance_tracking': os.getenv('PERFORMANCE_TRACKING', 'true').lower() == 'true',
            'response_time_limit': int(os.getenv('RESPONSE_TIME_LIMIT', '30')),
            
            # Streamlit Configuration
            'streamlit_port': int(os.getenv('STREAMLIT_PORT', '8667')),
            'streamlit_address': os.getenv('STREAMLIT_ADDRESS', '0.0.0.0'),
            
            # Feature Flags
            'enable_caching': os.getenv('ENABLE_CACHING', 'true').lower() == 'true',
            'enable_query_validation': os.getenv('ENABLE_QUERY_VALIDATION', 'true').lower() == 'true',
            'enable_result_formatting': os.getenv('ENABLE_RESULT_FORMATTING', 'true').lower() == 'true',
            'enable_german_validation': os.getenv('ENABLE_GERMAN_VALIDATION', 'true').lower() == 'true',
        }
    
    def _setup_logging(self):
        """Konfiguriert umfassendes Logging für WINCASA Layer 2"""
        log_level = getattr(logging, self._config['log_level'].upper())
        
        # Erstelle Logs-Verzeichnis falls es nicht existiert
        log_file = self._config['log_file']
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Comprehensive log format with more details
        detailed_format = '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s'
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # File Handler - Detailed logging
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(detailed_format))
        root_logger.addHandler(file_handler)
        
        # Console Handler - Simplified for readability
        console_format = '%(asctime)s | %(levelname)-8s | %(message)s'
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO if log_level < logging.INFO else log_level)
        console_handler.setFormatter(logging.Formatter(console_format))
        root_logger.addHandler(console_handler)
        
        # Error Handler - Separate file for errors only
        error_file = log_file.replace('.log', '_errors.log')
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(detailed_format))
        root_logger.addHandler(error_handler)
        
        # API Handler - Separate file for LLM API calls
        api_file = log_file.replace('.log', '_api.log')
        api_handler = logging.FileHandler(api_file, encoding='utf-8')
        api_handler.setLevel(logging.DEBUG)
        api_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | API_CALL | %(message)s'
        ))
        
        # Add API handler to specific loggers
        api_logger = logging.getLogger('llm_handler')
        api_logger.addHandler(api_handler)
        api_logger.setLevel(logging.DEBUG)
        
        # Performance Handler - For timing information
        perf_file = log_file.replace('.log', '_performance.log')
        perf_handler = logging.FileHandler(perf_file, encoding='utf-8')
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(logging.Formatter(
            '%(asctime)s | PERFORMANCE | %(message)s'
        ))
        
        perf_logger = logging.getLogger('performance')
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
        
        # Initial log message
        root_logger.info("="*80)
        root_logger.info("WINCASA Layer 2 System gestartet")
        root_logger.info(f"Log Level: {log_level}")
        root_logger.info(f"System Mode: {self._config['system_mode']}")
        root_logger.info(f"LLM Provider: {self._config['llm_provider']}")
        root_logger.info(f"Log Files: {log_file}, {error_file}, {api_file}, {perf_file}")
        root_logger.info("="*80)
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Gibt OpenAI LLM-Konfiguration zurück"""
        return {
            'provider': 'openai',
            'api_key': self._config['openai_api_key'],
            'model': self._config['openai_model'],
            'temperature': self._config['openai_temperature'],
            'max_tokens': self._config['openai_max_tokens']
        }
    
    def get_system_prompt_path(self) -> str:
        """Gibt Pfad zur System-Prompt-Datei basierend auf SYSTEM_MODE zurück"""
        mode = self._config['system_mode']
        # Fix: Ensure we're looking in the correct directory where prompts actually exist
        base_path = Path(__file__).parent  # This is src/wincasa/utils/
        
        prompt_files = {
            'json_standard': base_path / 'VERSION_A_JSON_SYSTEM.md',
            'json_vanilla': base_path / 'VERSION_A_JSON_VANILLA.md',
            'sql_standard': base_path / 'VERSION_B_SQL_SYSTEM.md',
            'sql_vanilla': base_path / 'VERSION_B_SQL_VANILLA.md'
        }
        
        if mode not in prompt_files:
            raise ValueError(f"Unbekannter System Mode: {mode}")
        
        return str(prompt_files[mode])
    
    def load_system_prompt(self) -> str:
        """Lädt System-Prompt basierend auf SYSTEM_MODE"""
        try:
            prompt_path = self.get_system_prompt_path()
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # VERSION files contain the prompt directly, not in code blocks
                # Just return the full content
                return content.strip()
                    
        except FileNotFoundError:
            # Silently ignore and let the caller handle with fallback
            # Don't log here to avoid noise in logs
            return None
        except Exception as e:
            # Only log unexpected errors
            logger.error(f"Unexpected error loading system prompt: {e}")
            return None
    
    def get_db_config(self) -> Dict[str, str]:
        """Gibt Datenbank-Konfiguration zurück"""
        return {
            'database': self._config['db_path'],
            'user': self._config['db_user'],
            'password': self._config['db_password'],
            'charset': self._config['db_charset']
        }
    
    def get_json_config(self) -> Dict[str, Any]:
        """Gibt JSON-Export-Konfiguration zurück"""
        return {
            'export_dir': self._config['json_export_dir'],
            'auto_export': self._config['json_auto_export']
        }
    
    def get_scheduler_config(self) -> Dict[str, Any]:
        """Gibt Scheduler-Konfiguration zurück"""
        return {
            'enabled': self._config['scheduler_enabled'],
            'interval': self._config['scheduler_interval'],
            'time': self._config['scheduler_time'],
            'timezone': self._config['scheduler_timezone'],
            'max_retries': self._config['scheduler_max_retries'],
            'cleanup_days': self._config['scheduler_cleanup_days']
        }
    
    def is_sql_mode(self) -> bool:
        """Prüft ob aktueller Mode SQL-basiert ist"""
        return self._config['system_mode'].startswith('sql_')
    
    def is_json_mode(self) -> bool:
        """Prüft ob aktueller Mode JSON-basiert ist"""
        return self._config['system_mode'].startswith('json_')
    
    def is_vanilla_mode(self) -> bool:
        """Prüft ob aktueller Mode Vanilla ist"""
        return self._config['system_mode'].endswith('_vanilla')
    
    def get_streamlit_config(self) -> Dict[str, Any]:
        """Gibt Streamlit-Konfiguration zurück"""
        return {
            'port': self._config['streamlit_port'],
            'address': self._config['streamlit_address']
        }
    
    def get(self, key: str, default=None):
        """Gibt Konfigurationswert zurück"""
        return self._config.get(key, default)
    
    def __getitem__(self, key: str):
        """Ermöglicht dict-ähnlichen Zugriff"""
        return self._config[key]


# Globale Konfigurationsinstanz
config = WincasaConfig()


def get_config() -> WincasaConfig:
    """Gibt globale Konfigurationsinstanz zurück"""
    return config


if __name__ == "__main__":
    # Test der Konfiguration
    cfg = WincasaConfig()
    
    print("=== WINCASA Layer 2 Configuration ===")
    print(f"LLM Provider: {cfg.get('llm_provider')}")
    print(f"System Mode: {cfg.get('system_mode')}")
    print(f"SQL Mode: {cfg.is_sql_mode()}")
    print(f"JSON Mode: {cfg.is_json_mode()}")
    print(f"Vanilla Mode: {cfg.is_vanilla_mode()}")
    print(f"System Prompt Path: {cfg.get_system_prompt_path()}")
    
    print("\n=== LLM Configuration ===")
    llm_config = cfg.get_llm_config()
    for key, value in llm_config.items():
        if 'api_key' in key:
            value = f"{value[:8]}..." if value else "Not set"
        print(f"{key}: {value}")
    
    print("\n=== System Prompt Preview ===")
    try:
        prompt = cfg.load_system_prompt()
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
    except Exception as e:
        print(f"Fehler beim Laden des System-Prompts: {e}")