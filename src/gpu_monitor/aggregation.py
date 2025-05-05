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

# gpu_monitor/aggregation.py
import statistics
import json
from typing import List, Dict, Any
from .logging import log_message

def aggregate_gpu_data(collections: List[List[Dict[str, Any]]], verbose: bool = False) -> List[Dict[str, Any]]:
    if not collections:
        log_message("No collections to aggregate", verbose=verbose)
        return []
    device_data = {}
    for collection in collections:
        for gpu in collection:
            device_id = gpu["device_id"]
            if device_id not in device_data:
                device_data[device_id] = []
            device_data[device_id].append(gpu)
    aggregated_data = []
    for device_id, gpu_list in device_data.items():
        aggregated_gpu = {"device_id": device_id, "name": gpu_list[-1]["name"]}
        numeric_keys = [k for k, v in gpu_list[0].items() if isinstance(v, (int, float))]
        for key in numeric_keys:
            values = [gpu[key] for gpu in gpu_list if key in gpu]
            if values:
                aggregated_gpu[f"{key}_mean"] = statistics.mean(values)
                aggregated_gpu[f"{key}_min"] = min(values)
                aggregated_gpu[f"{key}_max"] = max(values)
        aggregated_data.append(aggregated_gpu)
    log_message(f"Aggregated GPU data: {json.dumps(aggregated_data)}", verbose=verbose)
    return aggregated_data
