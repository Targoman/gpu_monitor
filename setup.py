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

# setup.py
from setuptools import setup, find_packages
import os
import sys

# Check Python version
if sys.version_info < (3, 6):
    sys.exit("Python 3.6 or higher is required")

# Check if running on Windows
is_windows = sys.platform.startswith('win')

setup(
    name="gpu_monitor",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pynvml>=11.0.0",
        "requests>=2.25.0"
    ],
    extras_require={
        ':sys_platform == "win32"': [
            "colorama>=0.4.1",
        ],
        ':python_version < "3.8"': [
            "typing-extensions>=3.7.4",
        ],
    },
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Hardware",
    ],
    entry_points={
        "console_scripts": [
            "gpu_monitor=gpu_monitor.main:main",
        ],
    },
    author="Targoman Intelligent Processing Co.",
    author_email="oss@targoman.com",
    description="A Python package for monitoring Nvidia GPU metrics",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/targoman/gpu_monitor",
    project_urls={
        "Bug Tracker": "https://github.com/targoman/gpu_monitor/issues",
        "Documentation": "https://github.com/targoman/gpu_monitor/wiki",
        "Source Code": "https://github.com/targoman/gpu_monitor",
    },
)
