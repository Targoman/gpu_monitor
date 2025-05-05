import unittest
import json
import os
import tempfile
from datetime import datetime, timedelta
from gpu_monitor.db import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test database
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_file = os.path.join(self.test_dir.name, "test.db")
        self.db = Database(self.db_file)

    def tearDown(self):
        # Clean up
        self.test_dir.cleanup()

    def test_store_and_load_raw_data(self):
        """Test storing and loading raw GPU data."""
        # Create sample GPU data
        gpu_data = {
            "gpus": [{
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
        }

        # Store data
        collection_id = self.db.save_collection(gpu_data)
        self.assertIsNotNone(collection_id)

        # Get data for aggregation
        start_time = (datetime.now() - timedelta(minutes=1)).isoformat()
        end_time = datetime.now().isoformat()
        collections = self.db.get_collections_for_aggregation(start_time, end_time)
        self.assertEqual(len(collections), 1)
        self.assertEqual(collections[0], gpu_data)

    def test_aggregated_data(self):
        """Test aggregated data storage and retrieval."""
        # Create sample aggregated data
        aggregated_data = {
            "gpus": [{
                "device_id": "GPU-1234",
                "name": "NVIDIA GeForce RTX 3080",
                "avg_memory_used_mb": 5120,
                "avg_sm_utilization_percent": 75,
                "avg_memory_utilization_percent": 60,
                "avg_temperature_celsius": 65,
                "avg_fan_speed_percent": 50,
                "avg_power_usage_watts": 200,
                "avg_graphics_clock_mhz": 1800,
                "avg_memory_clock_mhz": 9500
            }]
        }
        aggregation_time = datetime.now().replace(minute=0, second=0, microsecond=0).isoformat()

        # Store aggregated data
        data_id = self.db.save_aggregated_data(aggregated_data, aggregation_time)
        self.assertIsNotNone(data_id)

        # Get unsent data
        unsent_data = self.db.get_unsent_aggregated_data()
        self.assertEqual(len(unsent_data), 1)
        self.assertEqual(unsent_data[0]['data'], json.dumps(aggregated_data))

    def test_send_attempts(self):
        """Test send attempt recording and retrieval."""
        aggregation_time = datetime.now().replace(minute=0, second=0, microsecond=0).isoformat()
        
        # Record successful attempt
        self.db.record_send_attempt(
            aggregation_time=aggregation_time,
            success=True,
            uid="test-uid-1",
            params=json.dumps({"test": "data1"})
        )

        # Record failed attempt
        self.db.record_send_attempt(
            aggregation_time=aggregation_time,
            success=False,
            error="Test error",
            params=json.dumps({"test": "data2"})
        )

        # Get attempts
        attempts = self.db.get_send_attempts(aggregation_time)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0]['attempt_number'], 1)
        self.assertEqual(attempts[1]['attempt_number'], 2)
        self.assertTrue(attempts[0]['success'])
        self.assertFalse(attempts[1]['success'])

    def test_data_retention(self):
        """Test data retention policies."""
        # Create old data
        old_time = (datetime.now() - timedelta(days=31)).isoformat()
        recent_time = (datetime.now() - timedelta(days=1)).isoformat()
        old_aggregation_time = (datetime.now() - timedelta(days=366)).isoformat()
        recent_aggregation_time = (datetime.now() - timedelta(days=1)).isoformat()

        # Store old raw data
        old_data = {"gpus": [{"device_id": "GPU-1234", "test": "old"}]}
        self.db.save_collection(old_data)

        # Store recent raw data
        recent_data = {"gpus": [{"device_id": "GPU-1234", "test": "recent"}]}
        self.db.save_collection(recent_data)

        # Store old aggregated data
        old_aggregated = {"gpus": [{"device_id": "GPU-1234", "test": "old"}]}
        self.db.save_aggregated_data(old_aggregated, old_aggregation_time)

        # Store recent aggregated data
        recent_aggregated = {"gpus": [{"device_id": "GPU-1234", "test": "recent"}]}
        self.db.save_aggregated_data(recent_aggregated, recent_aggregation_time)

        # Run cleanup
        self.db.cleanup_old_data()

        # Check that old data is deleted but recent data remains
        start_time = (datetime.now() - timedelta(days=2)).isoformat()
        end_time = datetime.now().isoformat()
        collections = self.db.get_collections_for_aggregation(start_time, end_time)
        self.assertEqual(len(collections), 1)
        self.assertEqual(collections[0], recent_data)

        # Check aggregated data
        unsent_data = self.db.get_unsent_aggregated_data()
        self.assertEqual(len(unsent_data), 1)
        self.assertEqual(unsent_data[0]['data'], json.dumps(recent_aggregated))

    def test_mark_aggregated_data_sent(self):
        """Test marking aggregated data as sent."""
        # Create and store aggregated data
        aggregated_data = {"gpus": [{"device_id": "GPU-1234", "test": "data"}]}
        aggregation_time = datetime.now().replace(minute=0, second=0, microsecond=0).isoformat()
        data_id = self.db.save_aggregated_data(aggregated_data, aggregation_time)

        # Mark as sent
        self.db.mark_aggregated_data_sent(data_id, True)
        unsent_data = self.db.get_unsent_aggregated_data()
        self.assertEqual(len(unsent_data), 0)

        # Mark as failed
        self.db.mark_aggregated_data_sent(data_id, False, "Test error")
        unsent_data = self.db.get_unsent_aggregated_data()
        self.assertEqual(len(unsent_data), 1)

if __name__ == '__main__':
    unittest.main() 