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

# gpu_monitor/nvml.py
import sys
import pynvml
from typing import Dict, Any
from .logging import log_message

def initialize_nvml(verbose: bool = False) -> None:
    """Initialize NVML library."""
    if sys.platform == 'darwin':
        log_message("NVML is not fully supported on macOS", level='warning', verbose=verbose)
        return

    try:
        pynvml.nvmlInit()
        log_message("NVML initialized successfully", verbose=verbose)
    except pynvml.NVMLError as e:
        log_message(f"Failed to initialize NVML: {str(e)}", level='error', verbose=verbose)
        raise

def get_gpu_info(verbose: bool = False) -> Dict[str, Any]:
    """Get GPU information using NVML."""
    gpu_info = {"gpus": []}
    
    try:
        device_count = pynvml.nvmlDeviceGetCount()
        if verbose:
            log_message(f"Found {device_count} GPU(s)", level='DEBUG')
        
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            if verbose:
                log_message(f"GPU {i}: {name}", level='DEBUG')
            
            # Get GPU metrics
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
            fan = pynvml.nvmlDeviceGetFanSpeed(handle)
            graphics_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
            memory_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            
            # Get GPU UUID
            gpu_uuid = pynvml.nvmlDeviceGetUUID(handle)
            gpu_uuid = gpu_uuid.decode('utf-8') if isinstance(gpu_uuid, bytes) else str(gpu_uuid)
            
            # Get PCI info
            pci_info = pynvml.nvmlDeviceGetPciInfo(handle)
            # Use busId directly as it's the most reliable PCI identifier
            pci_bus_id = pci_info.busId.decode('utf-8') if isinstance(pci_info.busId, bytes) else str(pci_info.busId)
            
            # Convert name to string if it's bytes
            gpu_name = name.decode('utf-8') if isinstance(name, bytes) else str(name)
            
            gpu_info["gpus"].append({
                "uid": gpu_uuid,
                "pci_bus_id": pci_bus_id,
                "name": gpu_name,
                "temperature": temp,
                "memory_used": memory.used,
                "memory_total": memory.total,
                "gpu_utilization": utilization.gpu,
                "memory_utilization": utilization.memory,
                "power_usage": power,
                "fan_speed": fan,
                "graphics_clock": graphics_clock,
                "memory_clock": memory_clock
            })
            
            if verbose:
                log_message(f"GPU {i} PCI Bus ID: {pci_bus_id}", level='DEBUG')
        
        return gpu_info
        
    except pynvml.NVMLError as e:
        log_message(f"Error getting GPU info: {str(e)}", level='error', verbose=verbose)
        raise

def shutdown_nvml(verbose: bool = False) -> None:
    """Shutdown NVML library."""
    if sys.platform == 'darwin':
        return

    try:
        pynvml.nvmlShutdown()
        log_message("NVML shutdown successfully", verbose=verbose)
    except pynvml.NVMLError as e:
        log_message(f"Error shutting down NVML: {str(e)}", level='error', verbose=verbose)
        raise 