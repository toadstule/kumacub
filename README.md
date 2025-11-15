# KumaCub

**Run local checks; push results to Uptime Kuma.**

KumaCub is a lightweight daemon that executes scheduled health checks and pushes the results to [Uptime Kuma](https://github.com/louislam/uptime-kuma). It supports Nagios-compatible check scripts and provides flexible configuration via TOML files or environment variables.

## Features

- **Scheduled Checks**: Run health checks at configurable intervals
- **Nagios Compatible**: Supports standard Nagios plugin output format
- **Uptime Kuma Integration**: Push check results directly to Uptime Kuma
- **Flexible Configuration**: Configure via TOML files or environment variables
- **Hot Reload**: Reload configuration without restarting (via SIGHUP)
- **Structured Logging**: JSON-formatted logs with configurable levels
- **Async Architecture**: Built on asyncio for efficient concurrent execution

## Installation

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/kumacub.git
cd kumacub

# Install dependencies
pip install -e .
```

### System Service Installation

For production deployments, install KumaCub as a systemd service:

```bash
# Create directories
sudo mkdir -p /opt/kumacub /etc/kumacub

# Install application
cd /opt/kumacub
sudo python3 -m venv .venv
sudo .venv/bin/pip install /path/to/kumacub

# Copy configuration
sudo cp /path/to/kumacub/config/kumacub.toml /etc/kumacub/config.toml
sudo chmod 600 /etc/kumacub/config.toml  # Protect tokens

# Install systemd service
sudo cp kumacubd.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable kumacubd
sudo systemctl start kumacubd

# Check status
sudo systemctl status kumacubd
sudo journalctl -u kumacubd -f
```

**Note**: The service runs as root by default since many system checks (disk usage, service status, etc.) require elevated privileges. If your checks don't require root access, you can modify the service file to run as an unprivileged user by adding `User=kumacub` and `Group=kumacub` to the `[Service]` section.

## Configuration

KumaCub uses a TOML configuration file. By default, it looks for `/etc/kumacub/config.toml`, but you can override this with the `CONFIG` environment variable.

### Example Configuration

```toml
# Logging configuration
[log]
level = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
structured = true  # Use JSON-formatted logs

# Define checks
[[checks]]
name = "disk usage"
executor.command = "/usr/lib/monitoring-plugins/check_disk"
executor.args = ["-c", "90"]
publisher.url = "https://uptime-kuma.example.com"
publisher.push_token = "your-push-token-here"
schedule.interval = 60  # Run every 60 seconds

[[checks]]
name = "system time (ntp)"
executor.command = "/usr/lib/monitoring-plugins/check_ntp_time"
executor.args = ["-H", "pool.ntp.org", "-c", "10"]
publisher.url = "https://uptime-kuma.example.com"
publisher.push_token = "your-push-token-here"
schedule.interval = 30

[[checks]]
name = "system load"
executor.command = "check_load"
executor.args = ["-c", "10", "-w", "10"]
executor.env = { "PATH" = "/usr/lib/monitoring-plugins" }
publisher.url = "https://uptime-kuma.example.com"
publisher.push_token = "your-push-token-here"
schedule.interval = 30
```

### Configuration Fields

#### Check Configuration

Each `[[checks]]` entry supports:

- **name**: Unique identifier for the check
- **executor.command**: Command to execute
- **executor.args**: Command arguments (optional, default: `[]`)
- **executor.env**: Environment variables (optional, default: `{}`)
- **parser.name**: Parser type (optional, default: `"nagios"`)
- **publisher.url**: Uptime Kuma instance URL
- **publisher.push_token**: Uptime Kuma push token
- **schedule.interval**: Check interval in seconds (default: `60`)

### Environment Variables

You can override any configuration value using environment variables with the `KUMACUB__` prefix:

```bash
# Override config file location
export CONFIG=/path/to/config.toml

# Override log level
export KUMACUB__LOG__LEVEL=DEBUG

# Override log format
export KUMACUB__LOG__STRUCTURED=false
```

## Usage

### Running the Daemon

```bash
# Run with default config
kumacubd

# Run with custom config
CONFIG=/path/to/config.toml kumacubd

# Run with debug logging
KUMACUB__LOG__LEVEL=DEBUG kumacubd
```

### Managing the Systemd Service

```bash
# Start the service
sudo systemctl start kumacubd

# Stop the service
sudo systemctl stop kumacubd

# Restart the service
sudo systemctl restart kumacubd

# Reload configuration without restarting
sudo systemctl reload kumacubd

# Check service status
sudo systemctl status kumacubd

# View logs
sudo journalctl -u kumacubd -f

# Enable on boot
sudo systemctl enable kumacubd

# Disable on boot
sudo systemctl disable kumacubd
```

### Signal Handling

- **SIGINT/SIGTERM**: Graceful shutdown
- **SIGHUP**: Reload configuration without restarting

```bash
# Reload configuration (manual process)
kill -HUP $(pgrep kumacubd)

# Or use systemd
sudo systemctl reload kumacubd
```

## Check Output Format

KumaCub supports the Nagios plugin output format:

```
SERVICE OUTPUT | OPTIONAL PERFDATA
LONG TEXT LINE 1
LONG TEXT LINE 2
```

### Exit Codes

- `0`: OK
- `1`: WARNING
- `2`: CRITICAL
- `3`: UNKNOWN

### Example Check Script

```bash
#!/bin/bash
# check_disk.sh - Simple disk usage check

USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "$USAGE" -gt 90 ]; then
    echo "CRITICAL - Disk usage at ${USAGE}% | usage=${USAGE}%;80;90"
    exit 2
elif [ "$USAGE" -gt 80 ]; then
    echo "WARNING - Disk usage at ${USAGE}% | usage=${USAGE}%;80;90"
    exit 1
else
    echo "OK - Disk usage at ${USAGE}% | usage=${USAGE}%;80;90"
    exit 0
fi
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run formatting and linting
make format check
```

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.
