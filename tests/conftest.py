import pytest
import os
import tempfile
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir

@pytest.fixture
def test_db(temp_dir):
    """Create a test database file"""
    db_file = os.path.join(temp_dir, "test.db")
    yield db_file

@pytest.fixture
def sample_gpu_data():
    """Sample GPU data for testing"""
    return [{
        "device_id": "GPU-1234",
        "name": "NVIDIA GeForce RTX 3080",
        "memory_total_mb": 10240,
        "memory_used_mb": 5120,
        "memory_free_mb": 5120,
        "sm_utilization_percent": 75,
        "memory_utilization_percent": 60,
        "temperature_celsius": 65,
        "fan_speed_percent": 50,
        "power_usage_watts": 200,
        "graphics_clock_mhz": 1800,
        "memory_clock_mhz": 9500
    }]

@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        "server": {
            "url": "https://example.com",
            "contract_number": "12345",
            "offline": False
        },
        "intervals": {
            "collection": 60,
            "aggregation": 3600,
            "send": 3600
        },
        "paths": {
            "database": "run/gpu_metrics.db",
            "log": "run/gpu_monitor.log"
        }
    } 