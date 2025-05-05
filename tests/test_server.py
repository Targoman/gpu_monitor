import unittest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
from gpu_monitor.server import ServerClient, send_aggregated_data, send_pending_data

class TestServerClient(unittest.TestCase):
    def setUp(self):
        self.server_url = "http://test-server.com"
        self.contract_number = "TEST-123"
        self.client = ServerClient(self.server_url, self.contract_number, verbose=True)
        self.db = MagicMock()

    def test_send_data_success(self):
        """Test successful data sending."""
        # Prepare test data
        data = {
            "gpus": [{
                "device_id": "GPU-1234",
                "name": "NVIDIA GeForce RTX 3080",
                "avg_memory_used_mb": 5120,
                "avg_sm_utilization_percent": 75
            }]
        }
        aggregation_time = datetime.now().isoformat()
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "uid": "test-uid-1",
            "params": data
        }
        
        # Test sending
        with patch('requests.Session.post', return_value=mock_response):
            success, error = self.client.send_data(data, aggregation_time, self.db)
            
            # Verify results
            self.assertTrue(success)
            self.assertIsNone(error)
            self.db.record_send_attempt.assert_called_once_with(
                aggregation_time=aggregation_time,
                success=True,
                error=None,
                uid="test-uid-1",
                params=json.dumps(data)
            )

    def test_send_data_failure(self):
        """Test failed data sending."""
        # Prepare test data
        data = {
            "gpus": [{
                "device_id": "GPU-1234",
                "name": "NVIDIA GeForce RTX 3080",
                "avg_memory_used_mb": 5120,
                "avg_sm_utilization_percent": 75
            }]
        }
        aggregation_time = datetime.now().isoformat()
        
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        # Test sending
        with patch('requests.Session.post', return_value=mock_response):
            success, error = self.client.send_data(data, aggregation_time, self.db)
            
            # Verify results
            self.assertFalse(success)
            self.assertIsNotNone(error)
            self.db.record_send_attempt.assert_called_once_with(
                aggregation_time=aggregation_time,
                success=False,
                error="Server returned non-200 status: 500",
                uid=None,
                params=json.dumps(data)
            )

    def test_send_data_retry_limit(self):
        """Test retry limit for data sending."""
        # Prepare test data
        data = {
            "gpus": [{
                "device_id": "GPU-1234",
                "name": "NVIDIA GeForce RTX 3080",
                "avg_memory_used_mb": 5120,
                "avg_sm_utilization_percent": 75
            }]
        }
        aggregation_time = datetime.now().isoformat()
        
        # Mock multiple failed attempts
        self.db.get_send_attempts.return_value = [
            {"attempt_number": i} for i in range(1, 11)
        ]
        
        # Test sending
        success, error = self.client.send_data(data, aggregation_time, self.db)
        
        # Verify results
        self.assertFalse(success)
        self.assertEqual(error, "Maximum retry attempts (10) reached")
        self.db.record_send_attempt.assert_not_called()

    def test_send_data_validation(self):
        """Test response validation."""
        # Prepare test data
        data = {
            "gpus": [{
                "device_id": "GPU-1234",
                "name": "NVIDIA GeForce RTX 3080",
                "avg_memory_used_mb": 5120,
                "avg_sm_utilization_percent": 75
            }]
        }
        aggregation_time = datetime.now().isoformat()
        
        # Test cases for invalid responses
        test_cases = [
            # Invalid JSON
            (MagicMock(status_code=200, json=MagicMock(side_effect=ValueError())),
             "Server response is not a valid JSON object"),
            
            # Missing UID
            (MagicMock(status_code=200, json=MagicMock(return_value={})),
             "Server response missing required 'uid' field"),
            
            # Data mismatch
            (MagicMock(status_code=200, json=MagicMock(return_value={
                "uid": "test-uid-1",
                "params": {"different": "data"}
            })),
             "Server response data does not match sent data")
        ]
        
        for mock_response, expected_error in test_cases:
            with patch('requests.Session.post', return_value=mock_response):
                success, error = self.client.send_data(data, aggregation_time, self.db)
                
                # Verify results
                self.assertFalse(success)
                self.assertEqual(error, expected_error)
                self.db.record_send_attempt.assert_called_with(
                    aggregation_time=aggregation_time,
                    success=False,
                    error=expected_error,
                    uid=None if "uid" not in mock_response.json.return_value else "test-uid-1",
                    params=json.dumps(data)
                )

class TestSendFunctions(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.server_url = "http://test-server.com"
        self.verbose = True

    def test_send_aggregated_data(self):
        """Test sending aggregated data."""
        # Prepare test data
        data = {
            "id": 1,
            "gpus": [{
                "device_id": "GPU-1234",
                "name": "NVIDIA GeForce RTX 3080",
                "avg_memory_used_mb": 5120,
                "avg_sm_utilization_percent": 75
            }]
        }
        aggregation_time = datetime.now().isoformat()
        
        # Mock successful send
        with patch('gpu_monitor.server.ServerClient.send_data', return_value=(True, None)):
            success = send_aggregated_data(data, aggregation_time, self.server_url, self.db, self.verbose)
            
            # Verify results
            self.assertTrue(success)
            self.db.mark_aggregated_data_sent.assert_called_once_with(data['id'], True)

    def test_send_pending_data(self):
        """Test sending pending data."""
        # Prepare test data
        unsent_data = [
            {
                "id": 1,
                "aggregation_time": datetime.now().isoformat(),
                "data": json.dumps({"gpus": [{"device_id": "GPU-1234"}]})
            },
            {
                "id": 2,
                "aggregation_time": datetime.now().isoformat(),
                "data": json.dumps({"gpus": [{"device_id": "GPU-5678"}]})
            }
        ]
        self.db.get_unsent_aggregated_data.return_value = unsent_data
        
        # Mock successful sends
        with patch('gpu_monitor.server.send_aggregated_data', return_value=True):
            send_pending_data(self.db, self.server_url, self.verbose)
            
            # Verify results
            self.assertEqual(self.db.get_unsent_aggregated_data.call_count, 1)
            self.assertEqual(self.db.mark_aggregated_data_sent.call_count, 2)

if __name__ == '__main__':
    unittest.main() 