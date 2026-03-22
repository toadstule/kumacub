# KumaCub

**Run local checks; push results to Uptime Kuma.**

KumaCub is a lightweight daemon that executes scheduled health checks and pushes the results to
[Uptime Kuma](https://github.com/louislam/uptime-kuma).
It supports Nagios-compatible check scripts and provides flexible configuration via TOML files or environment variables.

Nagios-compatible check scripts are easy to find (and easy to write). You can find more than 50 of them at the
[Monitoring Plugins](https://www.monitoring-plugins.org/) website alone. There are checks for local system metrics,
such as:

  - Disk space
  - Disk/RAID health 
  - Load averages
  - Processes
  - System clock (NTP)
  - and more...

KumaCub allows you to execute these plugins locally, and push the results to Uptime Kuma.

## Installation

### Arch Linux (AUR)

For Arch Linux users, you can install [kumacub](https://aur.archlinux.org/packages/kumacub) from the AUR.
Installing this way will also install the systemd unit file and a sample config file.

```bash
# Install from AUR (we'll use `yay` for this example)
yay -S kumacub

# Optionally, install the monitoring-plugins package
yay -S monitoring-plugins
```

### Manual Installation (PIP)

If your distro doesn't have a package available, you can install KumaCub manually.

```bash
sudo pip install kumacub
sudo kumacub install
```

### Quick Setup with uv

If you prefer to use [uv](https://github.com/astral-sh/uv), you can set up your systemd service to use uv to run
KumaCub.

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sudo sh
    ```
2. Create a systemd unit file `/etc/systemd/system/kumacub.service`:
    ```unit file (systemd)
    [Unit]
    Description=KumaCub - Run local checks and push results to Uptime Kuma
    Documentation=https://github.com/toadstule/kumacub
    After=network-online.target
    Wants=network-online.target
    
    [Service]
    ExecStart=/root/.local/bin/uv run --isolated --no-progress --python=3.13 --with kumacub kumacub daemon
    ExecReload=/bin/kill -HUP $MAINPID
    
    [Install]
    WantedBy=multi-user.target   
    ```
3. Create a config file `/etc/kumacub/config.toml`:
   (see [Configuration](#configuration))
4. Reload systemd daemon:
    ```bash
    sudo systemctl daemon-reload
    ```

## Configuration

KumaCub uses TOML configuration files. By default, it looks for `/etc/kumacub/config.toml`, but you can override this
with the `KUMACUB__CONFIG` environment variable.

### Configuration Sources

KumaCub supports multiple configuration sources that are merged in order of priority (highest to lowest):

1. **Environment variables** (`KUMACUB__*`)
2. **Main TOML file** (`KUMACUB__CONFIG`, default: `/etc/kumacub/config.toml`)
3. **Configuration directory** (`KUMACUB__CONFIG_DIR`, default: `/etc/kumacub/conf.d/`)

### Configuration Directory

You can place multiple TOML files in the configuration directory (`/etc/kumacub/conf.d/` by default). All `.toml` files in this directory will be loaded and merged in alphabetical order. Later files override earlier values.

```bash
# Override config directory location
export KUMACUB__CONFIG_DIR=/path/to/conf.d/

# Example directory structure:
/etc/kumacub/
├── config.toml                 # Base configuration (logging, etc.)
└── conf.d/
    ├── 01_disk_usage.toml      # Disk usage check
    ├── 02_system_time.toml     # NTP check
    ├── 03_system_load.toml     # Load average check
    └── 99_production_overrides.toml  # Environment overrides
```

This approach is useful for:
- Splitting large configurations into logical sections
- Package managers that drop config files
- Environment-specific overrides
- Modular configuration management

### Example Configuration

#### Single File Configuration

For simple setups, you can use a single configuration file:

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

#### Split Configuration (Directory-based)

For more complex setups, you can split configuration across multiple files:

**/etc/kumacub/config.toml** (base configuration):
```toml
# Base logging configuration
[log]
level = "INFO"
structured = true
```

**/etc/kumacub/conf.d/01_disk_usage.toml:**
```toml
[[checks]]
name = "disk usage"
executor.command = "/usr/lib/monitoring-plugins/check_disk"
executor.args = ["-c", "90"]
publisher.url = "https://uptime-kuma.example.com"
publisher.push_token = "your-push-token-here"
schedule.interval = 60
```

**/etc/kumacub/conf.d/02_system_time.toml:**
```toml
[[checks]]
name = "system time (ntp)"
executor.command = "/usr/lib/monitoring-plugins/check_ntp_time"
executor.args = ["-H", "pool.ntp.org", "-c", "10"]
publisher.url = "https://uptime-kuma.example.com"
publisher.push_token = "your-push-token-here"
schedule.interval = 30
```

**/etc/kumacub/conf.d/03_system_load.toml:**
```toml
[[checks]]
name = "system load"
executor.command = "check_load"
executor.args = ["-c", "10", "-w", "10"]
executor.env = { "PATH" = "/usr/lib/monitoring-plugins" }
publisher.url = "https://uptime-kuma.example.com"
publisher.push_token = "your-push-token-here"
schedule.interval = 30
```

**/etc/kumacub/conf.d/99_production_overrides.toml:**
```toml
# Production environment overrides
[log]
level = "WARNING"
```

### Configuration Fields

#### Check Configuration

Each `[[checks]]` entry supports:

- **name**: Unique identifier for the check
- **executor.command**: Command to execute
- **executor.args**: Command arguments (optional, default: `[]`)
- **executor.env**: Environment variables (optional, default: `{}`)
- **publisher.url**: Uptime Kuma instance URL
- **publisher.push_token**: Uptime Kuma push token
- **schedule.interval**: Check interval in seconds (default: `60`)

### Environment Variables

You can override any configuration value using environment variables with the `KUMACUB__` prefix:

```bash
# Override config file location
export KUMACUB__CONFIG=/path/to/config.toml

# Override config directory location
export KUMACUB__CONFIG_DIR=/path/to/conf.d/

# Override log level
export KUMACUB__LOG__LEVEL=DEBUG

# Override log format
export KUMACUB__LOG__STRUCTURED=false
```

## Usage

### Managing the Systemd Service

```bash
# Start the service
sudo systemctl start kumacub

# Stop the service
sudo systemctl stop kumacub

# Restart the service
sudo systemctl restart kumacub

# Reload configuration without restarting
sudo systemctl reload kumacub

# Check service status
sudo systemctl status kumacub

# View logs
sudo journalctl -u kumacub -f

# Enable on boot
sudo systemctl enable kumacub

# Disable on boot
sudo systemctl disable kumacub
```

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
License as published by the Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see
<https://www.gnu.org/licenses/>.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.
