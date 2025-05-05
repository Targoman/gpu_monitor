import unittest
import json
from datetime import datetime, timedelta
from gpu_monitor.aggregation import aggregate_gpu_data

class TestAggregation(unittest.TestCase):
    def setUp(self):
        # Sample GPU data for testing
        self.gpu_data = [
            # First collection
            [{
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
            }],
            # Second collection
            [{
                "device_id": "GPU-1234",
                "name": "NVIDIA GeForce RTX 3080",
                "memory_total_mb": 10240,
                "memory_used_mb": 6144,
                "memory_free_mb": 4096,
                "sm_utilization_percent": 82,
                "memory_utilization_percent": 65,
                "temperature_celsius": 68,
                "fan_speed_percent": 55,
                "power_usage_watts": 220,
                "graphics_clock_mhz": 1850,
                "memory_clock_mhz": 9600
            }]
        ]

    def test_basic_aggregation(self):
        """Test basic aggregation of GPU data"""
        # Aggregate data
        aggregated = aggregate_gpu_data(self.gpu_data, verbose=False)

        # Verify results
        self.assertEqual(len(aggregated), 1)  # One GPU
        gpu = aggregated[0]

        # Check non-numeric fields
        self.assertEqual(gpu["device_id"], "GPU-1234")
        self.assertEqual(gpu["name"], "NVIDIA GeForce RTX 3080")

        # Check numeric fields
        self.assertEqual(gpu["memory_total_mb"], 10240)  # Should be constant
        self.assertAlmostEqual(gpu["memory_used_mb_mean"], 5632)  # (5120 + 6144) / 2
        self.assertEqual(gpu["memory_used_mb_min"], 5120)
        self.assertEqual(gpu["memory_used_mb_max"], 6144)

        self.assertAlmostEqual(gpu["sm_utilization_percent_mean"], 78.5)  # (75 + 82) / 2
        self.assertEqual(gpu["sm_utilization_percent_min"], 75)
        self.assertEqual(gpu["sm_utilization_percent_max"], 82)

    def test_empty_collections(self):
        """Test aggregation with empty collections"""
        # Test with empty list
        aggregated = aggregate_gpu_data([], verbose=False)
        self.assertEqual(len(aggregated), 0)

        # Test with list of empty collections
        aggregated = aggregate_gpu_data([[], []], verbose=False)
        self.assertEqual(len(aggregated), 0)

    def test_missing_values(self):
        """Test aggregation with missing values"""
        # Create data with missing values
        incomplete_data = [
            [{
                "device_id": "GPU-1234",
                "name": "NVIDIA GeForce RTX 3080",
                "memory_total_mb": 10240,
                "memory_used_mb": 5120,
                # Missing other fields
            }],
            [{
                "device_id": "GPU-1234",
                "name": "NVIDIA GeForce RTX 3080",
                "memory_total_mb": 10240,
                "memory_used_mb": 6144,
                "sm_utilization_percent": 82,
                # Missing other fields
            }]
        ]

        # Aggregate data
        aggregated = aggregate_gpu_data(incomplete_data, verbose=False)

        # Verify results
        self.assertEqual(len(aggregated), 1)
        gpu = aggregated[0]

        # Check that only available fields are aggregated
        self.assertEqual(gpu["device_id"], "GPU-1234")
        self.assertEqual(gpu["name"], "NVIDIA GeForce RTX 3080")
        self.assertEqual(gpu["memory_total_mb"], 10240)
        self.assertAlmostEqual(gpu["memory_used_mb_mean"], 5632)
        self.assertAlmostEqual(gpu["sm_utilization_percent_mean"], 82)

    def test_multiple_gpus(self):
        """Test aggregation with multiple GPUs"""
        # Create data for two GPUs
        multi_gpu_data = [
            [
                {
                    "device_id": "GPU-1234",
                    "name": "NVIDIA GeForce RTX 3080",
                    "memory_used_mb": 5120,
                    "sm_utilization_percent": 75
                },
                {
                    "device_id": "GPU-5678",
                    "name": "NVIDIA GeForce RTX 3090",
                    "memory_used_mb": 12288,
                    "sm_utilization_percent": 85
                }
            ],
            [
                {
                    "device_id": "GPU-1234",
                    "name": "NVIDIA GeForce RTX 3080",
                    "memory_used_mb": 6144,
                    "sm_utilization_percent": 82
                },
                {
                    "device_id": "GPU-5678",
                    "name": "NVIDIA GeForce RTX 3090",
                    "memory_used_mb": 14336,
                    "sm_utilization_percent": 88
                }
            ]
        ]

        # Aggregate data
        aggregated = aggregate_gpu_data(multi_gpu_data, verbose=False)

        # Verify results
        self.assertEqual(len(aggregated), 2)

        # Find each GPU in aggregated data
        gpu_3080 = next(g for g in aggregated if g["device_id"] == "GPU-1234")
        gpu_3090 = next(g for g in aggregated if g["device_id"] == "GPU-5678")

        # Check RTX 3080
        self.assertEqual(gpu_3080["name"], "NVIDIA GeForce RTX 3080")
        self.assertAlmostEqual(gpu_3080["memory_used_mb_mean"], 5632)
        self.assertAlmostEqual(gpu_3080["sm_utilization_percent_mean"], 78.5)

        # Check RTX 3090
        self.assertEqual(gpu_3090["name"], "NVIDIA GeForce RTX 3090")
        self.assertAlmostEqual(gpu_3090["memory_used_mb_mean"], 13312)
        self.assertAlmostEqual(gpu_3090["sm_utilization_percent_mean"], 86.5)

if __name__ == '__main__':
    unittest.main() 