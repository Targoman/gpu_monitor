# Copyright (C) 2025 Targoman Intelligent Processing Co.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# gpu_monitor/config.py
import os
import sys
import json
import argparse
from typing import Dict, Any

# Default configuration values
DEFAULT_INTERVALS = {
    'retry': 300,  # Retry interval in seconds (5 minutes)
    'collection': 60,  # Collection interval in seconds (1 minute)
    'aggregation': 3600  # Aggregation interval in seconds (1 hour)
}

# Handle path differences between operating systems
if sys.platform == 'win32':
    DEFAULT_PATHS = {
        'log': os.path.normpath('run\\gpu_monitor.log'),
        'database': os.path.normpath('run\\gpu_metrics.db')
    }
    CONFIG_DIR = os.path.normpath(os.path.expanduser('~\\.gpu_monitor'))
else:
    DEFAULT_PATHS = {
        'log': os.path.normpath('run/gpu_monitor.log'),
        'database': os.path.normpath('run/gpu_metrics.db')
    }
    CONFIG_DIR = os.path.normpath(os.path.expanduser('~/.gpu_monitor'))

DEFAULT_CONFIG = {
    'server': {
        'url': '',  # Leave empty for offline mode
        'contract_number': None,  # Required only in online mode
        'offline': True  # Default to offline mode
    },
    'intervals': DEFAULT_INTERVALS,
    'paths': DEFAULT_PATHS,
    'logging': {
        'level': 'INFO'  # Default logging level
    }
}

# Default configuration file paths
DEFAULT_CONFIG_PATHS = [
    'config.json',  # Current directory
    os.path.normpath(os.path.join(CONFIG_DIR, 'config.json')),  # User's home directory
    os.path.normpath('/etc/gpu_monitor/config.json')  # System-wide configuration
]

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='GPU Monitor')
    parser.add_argument('-c', '--config', help='Path to configuration file')
    parser.add_argument('-o', '--offline', action='store_true', help='Run in offline mode (don\'t send data to server)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('-l', '--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='Set logging level')
    parser.add_argument('-ls', '--list-sends', action='store_true', help='List all send attempts')
    parser.add_argument('-ss', '--search-send', help='Search send attempts by aggregation time (YYYY-MM-DD HH:00)')
    parser.add_argument('-sc', '--show-collection', help='Show raw collected data for a specific timestamp (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('-f', '--output-format', choices=['json', 'csv'], default='json',
                      help='Output format for collection data (default: json)')
    return parser.parse_args()

def load_config_file(config_path=None):  # type: (str) -> Dict[str, Any]
    """Load configuration from file."""
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config file {config_path}: {str(e)}")
            return DEFAULT_CONFIG

    # Try default config paths
    for path in DEFAULT_CONFIG_PATHS:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config file {path}: {str(e)}")
                continue

    return DEFAULT_CONFIG

def get_config(args):  # type: (argparse.Namespace) -> Dict[str, Any]
    """Get configuration from file and command line arguments."""
    # Load config from file
    config = load_config_file(args.config)

    # Override with command line arguments
    if args.offline:
        config['server']['url'] = ''
        config['server']['contract_number'] = None
        config['server']['offline'] = True

    # Set logging level from command line or config file
    if args.log_level:
        config['logging']['level'] = args.log_level
    elif args.verbose:
        config['logging']['level'] = 'DEBUG'

    # Platform-specific adjustments
    if sys.platform == 'darwin':
        # macOS-specific adjustments
        config['intervals']['collection'] = max(config['intervals']['collection'], 300)  # Minimum 5 minutes on macOS

    return config
