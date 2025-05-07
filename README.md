# GPU Monitor

A service for monitoring GPU metrics and sending them to a central server.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Platform-Specific Notes](#platform-specific-notes)
- [Configuration](#configuration)
- [Usage](#usage)
- [Data Flow](#data-flow)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Development](#development)
- [License](#license)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [Contact](#contact)

## Features

- Monitor NVIDIA GPU metrics including:
  - Memory usage (total, used, free)
  - SM and memory utilization
  - Temperature
  - Fan speed
  - Power usage
  - Clock speeds (graphics and memory)
- Aggregates metrics hourly
- Sends aggregated data to a central server
- Handles offline mode and retries
- Maintains data retention policies:
  - Raw data: 30 days
  - Aggregated data: 1 year
- Supports multiple GPUs
- Provides detailed logging
- Cross-platform support (Windows, Linux, macOS)
- Python 3.6+ compatibility

## Requirements

- Python 3.6 or higher
- NVIDIA GPU with NVIDIA drivers installed
- NVIDIA Management Library (NVML)

## Installation

### From PyPI

```bash
pip install gpu-monitor
```

### From Source

1. Clone the repository:
```bash
git clone https://github.com/targoman/gpu_monitor.git
cd gpu_monitor
```

2. Install dependencies:
```bash
pip install -e .
```

## Platform-Specific Notes

### Windows
- Colorama is automatically installed for Windows color support
- NVML is fully supported
- Windows 10 and 11 are supported
- Run as a Windows Service using NSSM (see [Running as a Service](#running-as-a-service))

### Linux
- NVML is fully supported
- Most Linux distributions are supported
- Run as a systemd service (see [Running as a Service](#running-as-a-service))

### macOS
- NVML has limited support on macOS
- Some GPU metrics may not be available
- Consider using alternative monitoring tools for macOS
- Run as a launchd service (see [Running as a Service](#running-as-a-service))

## Configuration

The tool can be configured using a JSON configuration file. By default, it looks for `config.json` in the current directory.

Example configuration:

```json
{
    "server": {
        "url": "https://example.com/api/metrics",
        "contract_number": "12345"
    },
    "collection": {
        "interval_seconds": 60,
        "aggregation_interval_hours": 1
    },
    "database": {
        "file": "gpu_metrics.db"
    },
    "logging": {
        "file": "gpu_monitor.log",
        "level": "INFO"
    }
}
```

## Usage

### Basic Usage

```bash
gpu_monitor
```

### Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--help` | `-h` | Show help message and exit |
| `--config CONFIG` | `-c` | Path to configuration file |
| `--offline` | `-o` | Run in offline mode (don't send data to server) |
| `--verbose` | `-v` | Enable verbose logging |
| `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}` | `-l` | Set logging level |
| `--list-sends` | `-ls` | List all send attempts |
| `--search-send SEARCH_SEND` | `-ss` | Search for a specific send attempt by time |
| `--show-collection SHOW_COLLECTION` | `-sc` | Show collection data for a specific time |
| `--output-format {json,csv}` | `-f` | Output format for collection data (default: json) |

### Usage Examples

#### Online Mode

1. Start monitoring with default settings:
```bash
gpu_monitor
```

2. View current GPU metrics in JSON format:
```bash
gpu_monitor --show-collection "" --output-format json
```
Example output:
```json
[
  {
    "timestamp": "2024-03-20T14:30:00",
    "gpus": [
      {
        "uid": "GPU-2e87a766-ac74-ea75-1dbe-13eb97066bd5",
        "pci_bus_id": "00000000:25:00.0",
        "name": "NVIDIA GeForce RTX 4090",
        "temperature": 29,
        "memory_used": 361431040,
        "memory_total": 24146608128,
        "gpu_utilization": 0,
        "memory_utilization": 0,
        "power_usage": 12.985,
        "fan_speed": 30,
        "graphics_clock": 210,
        "memory_clock": 405
      },
      {
        "uid": "GPU-1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
        "pci_bus_id": "00000000:26:00.0",
        "name": "NVIDIA H100",
        "temperature": 35,
        "memory_used": 4294967296,
        "memory_total": 85899345920,
        "gpu_utilization": 0,
        "memory_utilization": 0,
        "power_usage": 15.234,
        "fan_speed": 25,
        "graphics_clock": 180,
        "memory_clock": 350
      }
    ]
  }
]
```

3. View aggregated hourly data in CSV format:
```bash
gpu_monitor --show-collection "2024-03-20T14:00:00" --output-format csv
```
Example output:
```csv
timestamp,uid,pci_bus_id,name,temperature,memory_used,memory_total,gpu_utilization,memory_utilization,power_usage,fan_speed,graphics_clock,memory_clock
2024-03-20T14:00:00,GPU-2e87a766-ac74-ea75-1dbe-13eb97066bd5,00000000:25:00.0,NVIDIA GeForce RTX 4090,29,361431040,24146608128,0,0,12.985,30,210,405
2024-03-20T14:00:00,GPU-1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p,00000000:26:00.0,NVIDIA H100,35,4294967296,85899345920,0,0,15.234,25,180,350
```

#### Offline Mode

1. Start monitoring in offline mode:
```bash
gpu_monitor --offline
```

2. View send attempts history:
```bash
gpu_monitor --list-sends
```
Example output:
```
Send Attempts:
Aggregation Time | Attempts | First Attempt | Last Attempt | Last Error | UID | Sent
2024-03-20T13:00:00 | 3 | 2024-03-20T14:00:05 | 2024-03-20T14:00:15 | Connection timeout | abc123 | 0
2024-03-20T12:00:00 | 1 | 2024-03-20T13:00:05 | 2024-03-20T13:00:05 | None | def456 | 1
```

3. Search for specific send attempt:
```bash
gpu_monitor --search-send "2024-03-20T13:00:00"
```
Example output:
```
Send Attempt Details:
Aggregation Time: 2024-03-20T13:00:00
Attempts: 1
First Attempt: 2024-03-20T13:00:05
Last Attempt: 2024-03-20T13:00:05
Last Error: None
UID: def456
Sent: 1
```

4. View raw collection data for a specific time:
```bash
gpu_monitor --show-collection "2024-03-20T13:30:00" --output-format json
```
Example output:
```json
[
  {
    "timestamp": "2024-03-20T13:30:00",
    "gpus": [
      {
        "uid": "GPU-2e87a766-ac74-ea75-1dbe-13eb97066bd5",
        "pci_bus_id": "00000000:25:00.0",
        "name": "NVIDIA GeForce RTX 4090",
        "temperature": 29,
        "memory_used": 361431040,
        "memory_total": 24146608128,
        "gpu_utilization": 0,
        "memory_utilization": 0,
        "power_usage": 12.985,
        "fan_speed": 30,
        "graphics_clock": 210,
        "memory_clock": 405
      },
      {
        "uid": "GPU-1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
        "pci_bus_id": "00000000:26:00.0",
        "name": "NVIDIA H100",
        "temperature": 35,
        "memory_used": 4294967296,
        "memory_total": 85899345920,
        "gpu_utilization": 0,
        "memory_utilization": 0,
        "power_usage": 15.234,
        "fan_speed": 25,
        "graphics_clock": 180,
        "memory_clock": 350
      }
    ]
  }
]
```

### Running as a Service

#### Linux (systemd)

1. Install the systemd service:
```bash
sudo cp scripts/gpu-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
```

2. Start the service:
```bash
sudo systemctl start gpu-monitor
```

3. Enable auto-start:
```bash
sudo systemctl enable gpu-monitor
```

#### Windows (NSSM)

1. Download and install NSSM from [nssm.cc](https://nssm.cc/download)
2. Install the service:
```bash
nssm install GPU-Monitor "C:\Path\To\Python\python.exe" "C:\Path\To\gpu_monitor"
```
3. Start the service:
```bash
nssm start GPU-Monitor
```

#### macOS (launchd)

1. Create the service file:
```bash
cp scripts/com.targoman.gpu-monitor.plist ~/Library/LaunchAgents/
```
2. Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.targoman.gpu-monitor.plist
```

## Data Flow

1. **Collection**:
   - Collects raw GPU metrics every minute
   - Stores raw data in SQLite database
   - Raw data is retained for 30 days

2. **Aggregation**:
   - Aggregates raw data hourly
   - Calculates averages for all metrics
   - Stores aggregated data in SQLite database
   - Aggregated data is retained for 1 year

3. **Transmission**:
   - Sends aggregated data to central server
   - Implements retry logic (max 10 attempts)
   - Records all send attempts
   - Verifies data integrity with server response
   - Handles offline mode gracefully

## Error Handling

- **Collection Errors**:
  - Logs errors but continues operation
  - Retries on next collection cycle

- **Aggregation Errors**:
  - Logs errors but continues operation
  - Retries on next aggregation cycle

- **Transmission Errors**:
  - Implements retry logic (max 10 attempts)
  - Records all attempts in database
  - Verifies data integrity
  - Handles offline mode

## Logging

- Logs are written to both file and console
- Supports different log levels:
  - DEBUG: Detailed information for debugging
  - INFO: General operational information
  - WARNING: Warning messages for potential issues
  - ERROR: Error messages for serious problems
  - CRITICAL: Critical errors that may prevent operation
- Includes timestamps and color-coded output
- Control logging level via:
  - Command line: `--log-level LEVEL` or `-l LEVEL`
  - Config file: `logging.level` setting

## Development

### Setting Up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/targoman/gpu_monitor.git
cd gpu_monitor
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
python -m unittest discover tests
```

### Code Style

The project follows PEP 8 style guide. To check code style:

```bash
flake8 src tests
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Acknowledgments

- NVIDIA Management Library (NVML) for GPU monitoring capabilities
- The open-source community for various tools and libraries used in this project

## Contact

- Email: oss@targoman.com
- GitHub: [https://github.com/targoman/gpu_monitor](https://github.com/targoman/gpu_monitor)
- Documentation: [https://github.com/targoman/gpu_monitor/wiki](https://github.com/targoman/gpu_monitor/wiki)