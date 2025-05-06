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

# gpu_monitor/db.py
import os
import sys
import json
import sqlite3
import datetime
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class Database:
    """Database handler for GPU metrics."""
    
    def __init__(self, db_file: str, verbose: bool = False):
        """Initialize database connection."""
        self.verbose = verbose
        # Create database directory if it doesn't exist
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        if self.verbose:
            logger.debug(f"Opening database at: {os.path.abspath(db_file)}")
        
        # Connect to database
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row
        
        # Check if tables exist
        cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='collections'")
        if not cursor.fetchone():
            if self.verbose:
                logger.info("Creating database tables...")
            self._create_tables()
        elif self.verbose:
            logger.debug("Database tables already exist")
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        with self.conn:
            # Raw collections table (30 days retention)
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS collections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL,
                    sent INTEGER DEFAULT 0,
                    error TEXT
                )
            ''')
            
            # Log the schema only in verbose mode
            if self.verbose:
                cursor = self.conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='collections'")
                schema = cursor.fetchone()
                logger.info(f"Database schema for collections table:\n{schema[0]}")
            
            # Aggregated data table (1 year retention)
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS aggregated_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aggregation_time TEXT NOT NULL,
                    data TEXT NOT NULL,
                    sent INTEGER DEFAULT 0,
                    error TEXT
                )
            ''')
            
            # Send attempts table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS send_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aggregation_time TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    success INTEGER DEFAULT 0,
                    error TEXT,
                    uid TEXT,
                    params TEXT,
                    attempt_number INTEGER DEFAULT 1
                )
            ''')
    
    def save_collection(self, data: Dict[str, Any]) -> int:
        """Save raw GPU metrics collection."""
        timestamp = datetime.datetime.now().isoformat()
        data_json = json.dumps(data)
        
        if self.verbose:
            logger.debug(f"Saving collection to database with timestamp: {timestamp}")
            logger.debug(f"Data to save: {json.dumps(data, indent=2)}")
        
        with self.conn:
            cursor = self.conn.execute(
                'INSERT INTO collections (timestamp, data) VALUES (?, ?)',
                (timestamp, data_json)
            )
            row_id = cursor.lastrowid
            if self.verbose:
                logger.debug(f"Successfully saved collection with ID: {row_id}")
            logger.info(f"Saved GPU metrics for {len(data['gpus'])} GPUs")
            return row_id
    
    def save_aggregated_data(self, data: Dict[str, Any], aggregation_time: str) -> int:
        """Save aggregated GPU metrics."""
        data_json = json.dumps(data)
        
        with self.conn:
            cursor = self.conn.execute(
                'INSERT INTO aggregated_data (aggregation_time, data) VALUES (?, ?)',
                (aggregation_time, data_json)
            )
            return cursor.lastrowid
    
    def get_unsent_aggregated_data(self) -> List[Dict[str, Any]]:
        """Get all unsent aggregated data from the last 30 days."""
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
        
        with self.conn:
            cursor = self.conn.execute('''
                SELECT id, aggregation_time, data
                FROM aggregated_data
                WHERE sent = 0 AND aggregation_time > ?
                ORDER BY aggregation_time ASC
            ''', (cutoff_date,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_collections_for_aggregation(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """Get collections for a specific time range for aggregation."""
        with self.conn:
            cursor = self.conn.execute('''
                SELECT data
                FROM collections
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            ''', (start_time, end_time))
            return [json.loads(row['data']) for row in cursor.fetchall()]
    
    def mark_aggregated_data_sent(self, data_id: int, success: bool, error: Optional[str] = None) -> None:
        """Mark aggregated data as sent or failed."""
        with self.conn:
            if success:
                self.conn.execute(
                    'UPDATE aggregated_data SET sent = 1, error = NULL WHERE id = ?',
                    (data_id,)
                )
            else:
                self.conn.execute(
                    'UPDATE aggregated_data SET sent = 0, error = ? WHERE id = ?',
                    (error, data_id)
                )
    
    def record_send_attempt(self, aggregation_time: str, success: bool, error: Optional[str] = None,
                          uid: Optional[str] = None, params: Optional[str] = None) -> None:
        """Record a send attempt."""
        timestamp = datetime.datetime.now().isoformat()
        
        with self.conn:
            # Get attempt number
            cursor = self.conn.execute('''
                SELECT MAX(attempt_number) as max_attempt
                FROM send_attempts
                WHERE aggregation_time = ?
            ''', (aggregation_time,))
            row = cursor.fetchone()
            attempt_number = (row['max_attempt'] or 0) + 1
            
            # Insert attempt
            self.conn.execute('''
                INSERT INTO send_attempts (
                    aggregation_time, timestamp, success, error, uid, params, attempt_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (aggregation_time, timestamp, success, error, uid, params, attempt_number))
    
    def get_send_attempts(self, aggregation_time: str) -> List[Dict[str, Any]]:
        """Get all send attempts for a specific aggregation time."""
        with self.conn:
            cursor = self.conn.execute('''
                SELECT *
                FROM send_attempts
                WHERE aggregation_time = ?
                ORDER BY timestamp ASC
            ''', (aggregation_time,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_sends(self) -> List[Dict[str, Any]]:
        """Get all send attempts with summary information."""
        with self.conn:
            cursor = self.conn.execute('''
                SELECT 
                    aggregation_time,
                    COUNT(*) as attempts,
                    MIN(timestamp) as first_attempt,
                    MAX(timestamp) as last_attempt,
                    MAX(CASE WHEN success = 0 THEN error END) as last_error,
                    MAX(CASE WHEN success = 1 THEN uid END) as uid,
                    MAX(CASE WHEN success = 1 THEN 1 ELSE 0 END) as sent
                FROM send_attempts
                GROUP BY aggregation_time
                ORDER BY aggregation_time DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_send_by_time(self, aggregation_time: str) -> Optional[Dict[str, Any]]:
        """Get send attempt summary for a specific aggregation time."""
        with self.conn:
            cursor = self.conn.execute('''
                SELECT 
                    aggregation_time,
                    COUNT(*) as attempts,
                    MIN(timestamp) as first_attempt,
                    MAX(timestamp) as last_attempt,
                    MAX(CASE WHEN success = 0 THEN error END) as last_error,
                    MAX(CASE WHEN success = 1 THEN uid END) as uid,
                    MAX(CASE WHEN success = 1 THEN 1 ELSE 0 END) as sent
                FROM send_attempts
                WHERE aggregation_time = ?
                GROUP BY aggregation_time
            ''', (aggregation_time,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_collection_by_time(self, timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get raw collection data for a specific timestamp or current hour if no timestamp provided."""
        with self.conn:
            if timestamp is None:
                # Get current hour's data
                current_time = datetime.datetime.now()
                start_time = current_time.replace(minute=0, second=0, microsecond=0).isoformat()
                end_time = current_time.replace(minute=59, second=59, microsecond=999999).isoformat()
                
                if self.verbose:
                    logger.debug(f"Querying collections between {start_time} and {end_time}")
                
                # First check if we have any data in this range
                cursor = self.conn.execute('''
                    SELECT COUNT(*) as count
                    FROM collections
                    WHERE timestamp BETWEEN ? AND ?
                ''', (start_time, end_time))
                count = cursor.fetchone()['count']
                
                if count == 0:
                    # If no data found in current hour, get the most recent data
                    if self.verbose:
                        logger.debug("No data found in current hour, showing most recent data")
                    cursor = self.conn.execute('''
                        SELECT timestamp, data
                        FROM collections
                        ORDER BY timestamp DESC
                        LIMIT 1
                    ''')
                    latest = cursor.fetchone()
                    if latest:
                        data = json.loads(latest['data'])
                        if isinstance(data.get('gpus'), dict):
                            gpus_array = []
                            for gpu_id, gpu_data in data['gpus'].items():
                                gpu_data['uid'] = f"gpu_{gpu_id}_{gpu_data['name'].replace(' ', '_')}"
                                gpus_array.append(gpu_data)
                            data['gpus'] = gpus_array
                        return [{'timestamp': latest['timestamp'], **data}]
                    return []
                
                cursor = self.conn.execute('''
                    SELECT timestamp, data
                    FROM collections
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp ASC
                ''', (start_time, end_time))
            else:
                # Get data for specific timestamp
                if self.verbose:
                    logger.debug(f"Querying collections for timestamp {timestamp}")
                cursor = self.conn.execute('''
                    SELECT timestamp, data
                    FROM collections
                    WHERE timestamp = ?
                    ORDER BY timestamp ASC
                ''', (timestamp,))
            
            results = []
            for row in cursor.fetchall():
                data = json.loads(row['data'])
                # Convert old dictionary format to new array format
                if isinstance(data.get('gpus'), dict):
                    gpus_array = []
                    for gpu_id, gpu_data in data['gpus'].items():
                        gpu_data['uid'] = f"gpu_{gpu_id}_{gpu_data['name'].replace(' ', '_')}"
                        gpus_array.append(gpu_data)
                    data['gpus'] = gpus_array
                results.append({'timestamp': row['timestamp'], **data})
            
            if self.verbose:
                logger.debug(f"Found {len(results)} collections")
            return results
    
    def cleanup_old_data(self) -> None:
        """Clean up old data based on retention policies."""
        # Keep raw collections for 30 days
        collections_cutoff = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
        
        # Keep aggregated data for 1 year
        aggregated_cutoff = (datetime.datetime.now() - datetime.timedelta(days=365)).isoformat()
        
        with self.conn:
            # Delete old collections
            self.conn.execute(
                'DELETE FROM collections WHERE timestamp < ?',
                (collections_cutoff,)
            )
            
            # Delete old aggregated data
            self.conn.execute(
                'DELETE FROM aggregated_data WHERE aggregation_time < ?',
                (aggregated_cutoff,)
            )
            
            # Delete send attempts for deleted data
            self.conn.execute('''
                DELETE FROM send_attempts
                WHERE aggregation_time < ?
            ''', (aggregated_cutoff,))
    
    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
    
    def __del__(self):
        """Cleanup resources."""
        self.close()

    def check_database_contents(self) -> None:
        """Check and log all contents of the collections table."""
        with self.conn:
            cursor = self.conn.execute('SELECT COUNT(*) as count FROM collections')
            total_count = cursor.fetchone()['count']
            if self.verbose:
                logger.debug(f"Total collections in database: {total_count}")
            
            if total_count > 0:
                cursor = self.conn.execute('''
                    SELECT id, timestamp, data
                    FROM collections
                    ORDER BY timestamp DESC
                    LIMIT 5
                ''')
                recent_collections = cursor.fetchall()
                if self.verbose:
                    logger.debug("Most recent collections (raw data):")
                    for row in recent_collections:
                        logger.debug(f"ID: {row['id']}")
                        logger.debug(f"Timestamp: {row['timestamp']}")
                        logger.debug(f"Raw data: {row['data']}")
                        try:
                            data = json.loads(row['data'])
                            logger.debug(f"Parsed data: {json.dumps(data, indent=2)}")
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse data for ID {row['id']}")
                else:
                    logger.info(f"Found {total_count} collections in database")
