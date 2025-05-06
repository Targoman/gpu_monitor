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

# gpu_monitor/main.py
import time
import signal
import sys
import csv
import json
import os
from typing import Dict, Any, List
from .config import parse_args, get_config
from .logging import setup_logging, log_message
from .db import Database
from .nvml import initialize_nvml, get_gpu_info, shutdown_nvml
from .server import ServerClient

def format_collection_data(data, format_type='json'):  # type: (List[Dict[str, Any]], str) -> str
    """Format collection data in the specified format."""
    if format_type == 'csv':
        if not data:
            return "No data available"
        
        # Get fieldnames from first GPU entry
        fieldnames = ['timestamp']
        if data and data[0].get('gpus'):
            fieldnames.extend(data[0]['gpus'][0].keys())
        
        # Create CSV output
        output = []
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for entry in data:
            timestamp = entry['timestamp']
            for gpu in entry['gpus']:
                row = {'timestamp': timestamp}
                row.update(gpu)
                writer.writerow(row)
        
        return '\n'.join(output)
    else:  # json
        return json.dumps(data, indent=2)

def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_args()
    
    # Load configuration
    config = get_config(args)
    
    # Ensure run directory exists
    run_dir = os.path.dirname(config['paths']['log'])
    if not os.path.exists(run_dir):
        os.makedirs(run_dir)
    
    # Setup logging
    setup_logging(
        config['paths']['log'],
        level=config['logging']['level'],
        verbose=args.verbose
    )
    if args.verbose:
        log_message("Starting GPU Monitor", level='INFO')
    
    # Initialize database
    db = Database(config['paths']['database'], verbose=args.verbose)
    
    # Handle special commands
    if args.list_sends or args.search_send or args.show_collection is not None:
        # Database-only mode
        if args.list_sends:
            sends = db.get_all_sends()
            if not sends:
                print("No send attempts found")
                return
            
            print("\nSend Attempts:")
            print("Aggregation Time | Attempts | First Attempt | Last Attempt | Last Error | UID | Sent")
            for send in sends:
                print(f"{send['aggregation_time']} | {send['attempts']} | {send['first_attempt']} | {send['last_attempt']} | {send['last_error']} | {send['uid']} | {send['sent']}")
            return
        
        if args.search_send:
            send = db.get_send_by_time(args.search_send)
            if not send:
                print(f"No send attempt found for {args.search_send}")
                return
            
            print("\nSend Attempt Details:")
            print(f"Aggregation Time: {send['aggregation_time']}")
            print(f"Attempts: {send['attempts']}")
            print(f"First Attempt: {send['first_attempt']}")
            print(f"Last Attempt: {send['last_attempt']}")
            print(f"Last Error: {send['last_error']}")
            print(f"UID: {send['uid']}")
            print(f"Sent: {send['sent']}")
            return
        
        if args.show_collection is not None:
            # If show_collection is empty string, it means show current hour
            timestamp = None if args.show_collection == "" else args.show_collection
            collection_data = db.get_collection_by_time(timestamp)
            if collection_data:
                print(format_collection_data(collection_data, args.output_format))
            else:
                print(f"No collection data found for {timestamp if timestamp else 'current hour'}")
                if args.verbose:
                    db.check_database_contents()
            return
    
    # If we get here, we're in normal collection mode
    # Initialize NVML
    try:
        initialize_nvml(verbose=args.verbose)
    except Exception as e:
        log_message(f"Failed to initialize NVML: {str(e)}", level='ERROR')
        return
    
    # Initialize server client
    server = ServerClient(
        config['server']['url'],
        config['server']['contract_number'],
        config['server']['offline'],
        verbose=args.verbose
    )
    
    # Main loop
    try:
        while True:
            # Collect GPU metrics
            try:
                gpu_info = get_gpu_info(verbose=args.verbose)
                db.save_collection(gpu_info)
                log_message("GPU metrics collected", level='DEBUG')
            except Exception as e:
                log_message(f"Failed to collect GPU metrics: {str(e)}", level='ERROR')
            
            # Sleep until next collection
            time.sleep(config['intervals']['collection'])
            
    except KeyboardInterrupt:
        log_message("Shutting down...", level='INFO')
    finally:
        shutdown_nvml()
        db.close()
        log_message("Shutdown complete", level='INFO')

if __name__ == '__main__':
    main()
