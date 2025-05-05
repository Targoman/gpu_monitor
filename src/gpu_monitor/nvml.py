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
    """Get information about all GPUs."""
    try:
        # Get device count
        device_count = pynvml.nvmlDeviceGetCount()
        log_message(f"Found {device_count} GPU(s)", verbose=verbose)

        # Get information for each GPU
        gpus = {}
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            
            # Get basic info
            name = pynvml.nvmlDeviceGetName(handle)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
            
            # Get fan speed if available
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
            except pynvml.NVMLError:
                fan_speed = 0
            
            # Get clock speeds if available
            try:
                graphics_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                memory_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            except pynvml.NVMLError:
                graphics_clock = 0
                memory_clock = 0
            
            # Store GPU info
            gpus[str(i)] = {
                'name': name.decode('utf-8'),
                'temperature': temperature,
                'memory_used': memory_info.used,
                'memory_total': memory_info.total,
                'gpu_utilization': utilization.gpu,
                'memory_utilization': utilization.memory,
                'power_usage': power_usage,
                'fan_speed': fan_speed,
                'graphics_clock': graphics_clock,
                'memory_clock': memory_clock
            }
            
            log_message(f"GPU {i}: {name.decode('utf-8')}", verbose=verbose)

        return {'gpus': gpus}

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