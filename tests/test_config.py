import unittest
import json
import os
import tempfile
from pathlib import Path
from gpu_monitor.config import (
    get_config_path, load_config, is_offline_mode,
    DEFAULT_CONFIG, validate_config
)

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir.name)

    def tearDown(self):
        # Clean up
        os.chdir(self.original_cwd)
        self.test_dir.cleanup()

    def test_default_config(self):
        """Test that default config is correct"""
        config = load_config()
        self.assertEqual(config, DEFAULT_CONFIG)
        self.assertTrue(is_offline_mode(config))

    def test_offline_mode_conditions(self):
        """Test all conditions that trigger offline mode"""
        # Test 1: No config file
        config = load_config()
        self.assertTrue(is_offline_mode(config))

        # Test 2: Empty URL
        config = DEFAULT_CONFIG.copy()
        config['server']['url'] = ""
        self.assertTrue(is_offline_mode(config))

        # Test 3: Offline flag in config
        config = DEFAULT_CONFIG.copy()
        config['server']['offline'] = True
        self.assertTrue(is_offline_mode(config))

    def test_online_mode_conditions(self):
        """Test all conditions required for online mode"""
        # Create a valid online config
        config = DEFAULT_CONFIG.copy()
        config['server']['url'] = "https://example.com"
        config['server']['contract_number'] = "12345"
        config['server']['offline'] = False

        # Test validation
        self.assertTrue(validate_config(config))
        self.assertFalse(is_offline_mode(config))

    def test_invalid_online_config(self):
        """Test validation of invalid online configurations"""
        # Test 1: Missing contract number
        config = DEFAULT_CONFIG.copy()
        config['server']['url'] = "https://example.com"
        self.assertFalse(validate_config(config))

        # Test 2: Empty contract number
        config['server']['contract_number'] = ""
        self.assertFalse(validate_config(config))

        # Test 3: Invalid URL
        config['server']['url'] = "not-a-url"
        self.assertFalse(validate_config(config))

    def test_config_file_precedence(self):
        """Test config file location precedence"""
        # Create config files in different locations
        current_dir_config = Path("config.json")
        home_config = Path.home() / ".gpu_monitor" / "config.json"
        system_config = Path("/etc/gpu_monitor/config.json")

        # Test current directory config
        with open(current_dir_config, 'w') as f:
            json.dump({"test": "current"}, f)
        self.assertEqual(get_config_path(), current_dir_config)

        # Test home directory config
        current_dir_config.unlink()
        home_config.parent.mkdir(parents=True, exist_ok=True)
        with open(home_config, 'w') as f:
            json.dump({"test": "home"}, f)
        self.assertEqual(get_config_path(), home_config)

        # Test system config
        home_config.unlink()
        system_config.parent.mkdir(parents=True, exist_ok=True)
        with open(system_config, 'w') as f:
            json.dump({"test": "system"}, f)
        self.assertEqual(get_config_path(), system_config)

if __name__ == '__main__':
    unittest.main() 