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

# gpu_monitor/server.py
import sys
import json
import time
import requests
import threading
from typing import Dict, Any, Tuple, Optional, List
from .logging import log_message
from .db import Database
from datetime import datetime

class ServerClient:
    """Client for communicating with the metrics server."""
    
    def __init__(self, url: str, contract_number: str, offline: bool = True, verbose: bool = False):
        """Initialize server client."""
        self.url = url
        self.contract_number = contract_number
        self.offline = offline
        self.verbose = verbose
        self.session = requests.Session()
        self.timeout = 30  # 30 seconds timeout
        self.headers = {
            'Content-Type': 'application/json',
            'X-Contract-Number': contract_number
        }
        self.max_retries = 10  # Maximum number of retry attempts
    
    def send_data(self, data: Dict[str, Any], aggregation_time: str, db: Database) -> Tuple[bool, Optional[str]]:
        """Send data to server with retry logic."""
        if not self.url or self.offline:
            log_message("Server URL not configured or in offline mode, skipping send", level='warning', verbose=self.verbose)
            return True, None
        
        # Get previous attempts
        attempts = db.get_send_attempts(aggregation_time)
        if len(attempts) >= self.max_retries:
            error = f"Maximum retry attempts ({self.max_retries}) reached"
            log_message(error, level='error', verbose=self.verbose)
            return False, error
        
        try:
            # Add contract number to data
            data['contract_number'] = self.contract_number
            
            # Send data
            log_message(f"Sending data to server: {json.dumps(data)}", verbose=self.verbose)
            response = self.session.post(
                self.url,
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            
            # Check response
            if response.status_code == 200:
                response_json = response.json()
                
                # Validate response
                if not isinstance(response_json, dict):
                    error = "Server response is not a valid JSON object"
                    log_message(error, level='error', verbose=self.verbose)
                    db.record_send_attempt(aggregation_time, False, error, None, json.dumps(data))
                    return False, error
                
                if "uid" not in response_json:
                    error = "Server response missing required 'uid' field"
                    log_message(error, level='error', verbose=self.verbose)
                    db.record_send_attempt(aggregation_time, False, error, None, json.dumps(data))
                    return False, error
                
                # Verify data integrity
                if "params" in response_json and response_json["params"] != data:
                    error = "Server response data does not match sent data"
                    log_message(error, level='error', verbose=self.verbose)
                    db.record_send_attempt(aggregation_time, False, error, response_json["uid"], json.dumps(data))
                    return False, error
                
                # Record successful attempt
                log_message("Data sent successfully", verbose=self.verbose)
                db.record_send_attempt(aggregation_time, True, None, response_json["uid"], json.dumps(data))
                return True, None
            else:
                error = f"Server returned non-200 status: {response.status_code}"
                log_message(error, level='error', verbose=self.verbose)
                db.record_send_attempt(aggregation_time, False, error, None, json.dumps(data))
                return False, error
                
        except requests.RequestException as e:
            error = f"Failed to send data: {str(e)}"
            log_message(error, level='error', verbose=self.verbose)
            db.record_send_attempt(aggregation_time, False, error, None, json.dumps(data))
            return False, error
    
    def __del__(self):
        """Cleanup resources."""
        self.session.close()

def send_aggregated_data(data: Dict[str, Any], aggregation_time: str, server_url: str, db: Database, verbose: bool) -> bool:
    """Send aggregated data to server."""
    log_message(f"Sending data for {aggregation_time} to server: {json.dumps(data)}", verbose=verbose)
    
    # Create server client
    client = ServerClient(server_url, data.get('contract_number', ''), verbose=verbose)
    
    # Send data
    success, error = client.send_data(data, aggregation_time, db)
    
    # Update aggregated data status
    if 'id' in data:
        if success:
            db.mark_aggregated_data_sent(data['id'], True)
        else:
            db.mark_aggregated_data_sent(data['id'], False, error)
    
    return success

def send_pending_data(db, server_url: str, verbose: bool) -> None:
    """Send all pending aggregated data from the last 30 days."""
    # Get unsent data
    unsent_data = db.get_unsent_aggregated_data()
    
    # Send data in parallel
    threads = []
    for data in unsent_data:
        thread = threading.Thread(
            target=send_aggregated_data,
            args=(data, data['aggregation_time'], server_url, db, verbose)
        )
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
