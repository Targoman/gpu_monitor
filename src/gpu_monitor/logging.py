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

# gpu_monitor/logging.py
import os
import sys
import logging
from datetime import datetime
from typing import Optional

# Platform-specific color support
if sys.platform == 'win32':
    try:
        from colorama import Fore, Style, init
        init()
    except ImportError:
        class DummyColors:
            def __getattr__(self, name):
                return ''
        Fore = DummyColors()
        Style = DummyColors()
else:
    class Fore:
        BLACK = '\033[30m'
        RED = '\033[31m'
        GREEN = '\033[32m'
        YELLOW = '\033[33m'
        BLUE = '\033[34m'
        CYAN = '\033[36m'
        WHITE = '\033[37m'
    
    class Style:
        RESET_ALL = '\033[0m'
        BRIGHT = '\033[1m'

def setup_logging(log_file: str, level: str = 'INFO', verbose: bool = False) -> None:
    """Setup logging configuration."""
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure logging
    log_level = getattr(logging, level.upper())
    if verbose:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def log_message(message: str, level: str = 'info', verbose: bool = False) -> None:
    """Log a message with color-coded output."""
    level = level.upper()
    logger = logging.getLogger()
    
    # Get color based on level
    color = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }.get(level, Fore.WHITE)
    
    # Log with color
    if sys.platform != 'win32':
        message = f"{color}{message}{Style.RESET_ALL}"
    
    # Log to appropriate level
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message)

def log_offline_mode(verbose: bool = False) -> None:
    """Log offline mode message."""
    message = "Service is running in OFFLINE mode"
    log_message(message, level='critical', verbose=verbose) 