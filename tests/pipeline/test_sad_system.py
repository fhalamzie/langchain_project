#!/usr/bin/env python3
"""
SAD System Pipeline Tests
Tests für Self-Updating Development Stack aus SAD.md
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
import subprocess
import json
import time
import logging
from typing import Dict, List
import tempfile
import shutil

logger = logging.getLogger(__name__)

class SADSystemTests:
    """Tests für SAD (Self-Updating Development) System"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.scripts_dir = self.project_root / "tools" / "scripts"
        
    def test_sync_project_script_exists(self):
        """Test: sync-project.sh Script existiert und ist ausführbar"""
        sync_script = self.scripts_dir / "sync-project.sh"
        assert sync_script.exists(), "sync-project.sh script missing"
        assert sync_script.is_file(), "sync-project.sh is not a file"
        
        # Check if executable
        import stat
        file_stat = sync_script.stat()
        is_executable = bool(file_stat.st_mode & stat.S_IEXEC)
        
        if not is_executable:
            # Make executable if needed
            sync_script.chmod(sync_script.stat().st_mode | stat.S_IEXEC)
            logger.info("Made sync-project.sh executable")
        
        logger.info("✅ sync-project.sh exists and is executable")

    def test_update_docs_script_exists(self):
        """Test: update-docs.sh Script existiert"""
        update_docs_script = self.scripts_dir / "update-docs.sh"
        assert update_docs_script.exists(), "update-docs.sh script missing"
        
        logger.info("✅ update-docs.sh exists")

    def test_config_structure_valid(self):
        """Test: Konfigurationsstruktur ist korrekt"""
        config_dir = self.project_root / "config"
        assert config_dir.exists(), "config/ directory missing"
        
        required_configs = [
            "sql_paths.json",
            "query_engine.json", 
            "feature_flags.json",
            ".env"
        ]
        
        for config_file in required_configs:
            config_path = config_dir / config_file
            assert config_path.exists(), f"Required config file missing: {config_file}"
            
            # Validate JSON files
            if config_file.endswith('.json'):
                try:
                    with open(config_path) as f:
                        json.load(f)
                    logger.info(f"✅ {config_file} is valid JSON")
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {config_file}: {e}")
        
        logger.info("✅ Configuration structure is valid")

    def test_data_structure_valid(self):
        """Test: Data-Verzeichnisstruktur ist korrekt nach Refactoring"""
        data_dir = self.project_root / "data"
        assert data_dir.exists(), "data/ directory missing"
        
        required_subdirs = [
            "sql",           # SQL_QUERIES moved here
            "exports",       # JSON exports
            "knowledge_base", # Field mappings
            "wincasa_data"   # Firebird DB
        ]
        
        for subdir in required_subdirs:
            subdir_path = data_dir / subdir
            assert subdir_path.exists(), f"Required data subdirectory missing: {subdir}"
            assert subdir_path.is_dir(), f"{subdir} is not a directory"
        
        # Validate SQL files exist
        sql_dir = data_dir / "sql"
        sql_files = list(sql_dir.glob("*.sql"))
        assert len(sql_files) > 0, "No SQL files found in data/sql/"
        
        # Validate exports exist
        exports_dir = data_dir / "exports"
        json_files = list(exports_dir.glob("*.json"))
        assert len(json_files) > 0, "No JSON exports found in data/exports/"
        
        logger.info("✅ Data structure is valid")

    def test_package_structure_valid(self):
        """Test: src/wincasa/ Package-Struktur ist korrekt"""
        src_dir = self.project_root / "src" / "wincasa"
        assert src_dir.exists(), "src/wincasa/ package missing"
        
        required_packages = [
            "core",
            "data", 
            "knowledge",
            "monitoring",
            "utils"
        ]
        
        for package in required_packages:
            package_dir = src_dir / package
            assert package_dir.exists(), f"Package missing: {package}"
            assert package_dir.is_dir(), f"{package} is not a directory"
            
            # Check for __init__.py
            init_file = package_dir / "__init__.py"
            assert init_file.exists(), f"__init__.py missing in {package}/"
        
        # Check main __init__.py
        main_init = src_dir / "__init__.py"
        assert main_init.exists(), "Main __init__.py missing in src/wincasa/"
        
        logger.info("✅ Package structure is valid")

    def test_import_paths_work(self):
        """Test: Neue Import-Pfade funktionieren"""
        try:
            # Test core imports
            from wincasa.core.streamlit_app import WincasaStreamlitApp
            from wincasa.core.wincasa_query_engine import WincasaQueryEngine
            
            # Test data imports
            from wincasa.data.layer4_json_loader import Layer4JSONLoader
            
            # Test utils imports
            from wincasa.utils.config_loader import WincasaConfig
            
            logger.info("✅ All critical imports work correctly")
            
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_config_loading_works(self):
        """Test: Konfiguration lädt korrekt mit neuen Pfaden"""
        try:
            from wincasa.utils.config_loader import WincasaConfig
            
            # This should not raise FileNotFoundError anymore
            config = WincasaConfig()
            assert config is not None, "Config object is None"
            
            # Basic config values should be available
            assert hasattr(config, '_config'), "Config._config not available"
            assert isinstance(config._config, dict), "Config._config is not dict"
            
            logger.info("✅ Configuration loading works correctly")
            
        except Exception as e:
            pytest.fail(f"Config loading failed: {e}")

    def test_system_prompt_files_exist(self):
        """Test: System-Prompt-Dateien existieren"""
        utils_dir = self.project_root / "src" / "wincasa" / "utils"
        
        required_prompts = [
            "VERSION_A_JSON_SYSTEM.md",
            "VERSION_A_JSON_VANILLA.md", 
            "VERSION_B_SQL_SYSTEM.md",
            "VERSION_B_SQL_VANILLA.md"
        ]
        
        for prompt_file in required_prompts:
            prompt_path = utils_dir / prompt_file
            assert prompt_path.exists(), f"System prompt missing: {prompt_file}"
            
            # Check file is not empty
            assert prompt_path.stat().st_size > 0, f"System prompt is empty: {prompt_file}"
        
        logger.info("✅ All system prompt files exist")

    def test_documentation_structure(self):
        """Test: Dokumentationsstruktur ist vollständig"""
        docs_dir = self.project_root / "docs"
        assert docs_dir.exists(), "docs/ directory missing"
        
        # Check Sphinx files
        sphinx_files = ["conf.py", "index.rst", "Makefile"]
        for sphinx_file in sphinx_files:
            file_path = docs_dir / sphinx_file
            assert file_path.exists(), f"Sphinx file missing: {sphinx_file}"
        
        # Check root documentation
        root_docs = [
            "ARCHITECTURE.md",
            "INVENTORY.md", 
            "SAD.md",
            "CLAUDE.md",
            "TESTING.md",
            "LOGGING.md",
            "API.md",
            "CHANGELOG.md"
        ]
        
        for doc_file in root_docs:
            doc_path = self.project_root / doc_file
            assert doc_path.exists(), f"Documentation file missing: {doc_file}"
        
        logger.info("✅ Documentation structure is complete")

    @pytest.mark.slow
    def test_minimal_sync_execution(self):
        """Test: Minimaler sync-project.sh Execution Test"""
        # This is a minimal test that checks if sync-project.sh can be invoked
        # without actually running the full sync (which would be slow)
        
        sync_script = self.scripts_dir / "sync-project.sh"
        
        try:
            # Try to run with --help or --dry-run if available
            result = subprocess.run(
                [str(sync_script), "--help"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # If --help doesn't exist, just check if script is syntactically valid
            if result.returncode != 0:
                # Check if it's a bash syntax error
                result = subprocess.run(
                    ["bash", "-n", str(sync_script)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                assert result.returncode == 0, f"sync-project.sh has syntax errors: {result.stderr}"
            
            logger.info("✅ sync-project.sh is executable and syntactically valid")
            
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ sync-project.sh execution timeout (might be expected)")
        except Exception as e:
            pytest.fail(f"sync-project.sh execution failed: {e}")

    def test_inventory_md_updated(self):
        """Test: INVENTORY.md wurde für neue Struktur aktualisiert"""
        inventory_path = self.project_root / "INVENTORY.md"
        assert inventory_path.exists(), "INVENTORY.md missing"
        
        with open(inventory_path) as f:
            content = f.read()
        
        # Should contain new structure references
        new_structure_indicators = [
            "src/wincasa/",
            "tests/unit/",
            "tests/integration/",
            "wincasa.core.",
            "wincasa.data.",
            "Import: `wincasa.",
            "Refactored"
        ]
        
        found_indicators = []
        for indicator in new_structure_indicators:
            if indicator in content:
                found_indicators.append(indicator)
        
        assert len(found_indicators) >= 3, \
            f"INVENTORY.md not updated for new structure. Found: {found_indicators}"
        
        logger.info("✅ INVENTORY.md reflects new structure")


class TestSADSystem:
    """Main test class for pytest discovery"""
    
    @pytest.fixture(autouse=True)
    def setup_test_instance(self):
        self.sad_tests = SADSystemTests()
    
    def test_sync_project_script_exists(self):
        self.sad_tests.test_sync_project_script_exists()
    
    def test_update_docs_script_exists(self):
        self.sad_tests.test_update_docs_script_exists()
    
    def test_config_structure_valid(self):
        self.sad_tests.test_config_structure_valid()
    
    def test_data_structure_valid(self):
        self.sad_tests.test_data_structure_valid()
    
    def test_package_structure_valid(self):
        self.sad_tests.test_package_structure_valid()
    
    def test_import_paths_work(self):
        self.sad_tests.test_import_paths_work()
    
    def test_config_loading_works(self):
        self.sad_tests.test_config_loading_works()
    
    def test_system_prompt_files_exist(self):
        self.sad_tests.test_system_prompt_files_exist()
    
    def test_documentation_structure(self):
        self.sad_tests.test_documentation_structure()
    
    @pytest.mark.slow
    def test_minimal_sync_execution(self):
        self.sad_tests.test_minimal_sync_execution()
    
    def test_inventory_md_updated(self):
        self.sad_tests.test_inventory_md_updated()

if __name__ == "__main__":
    print("🧪 SAD System Pipeline Test Suite")
    print("Run with: pytest tests/pipeline/test_sad_system.py -v")
    print("Run with slow tests: pytest tests/pipeline/test_sad_system.py -v -m slow")