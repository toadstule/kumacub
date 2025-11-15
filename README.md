# KumaCub

**Run local checks; push results to Uptime Kuma.**

KumaCub is a lightweight daemon that executes scheduled health checks and pushes the results to [Uptime Kuma](https://github.com/louislam/uptime-kuma). It supports Nagios-compatible check scripts and provides flexible configuration via TOML files or environment variables.

## Installation

### Arch Linux (AUR)

For Arch Linux users, you can install KumaCub from the AUR. Installing this way will also install the systemd unit file
and a sample config file.

```bash
# Install from AUR (we'll use `yay` for this example)
yay -S kumacub
```

### Quick Setup with uv

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sudo sh
    ```
2. Create a systemd unit file `/etc/systemd/system/kumacubd.service`:
    ```unit file (systemd)
    [Unit]
    Description=KumaCub - Run local checks and push results to Uptime Kuma
    Documentation=https://github.com/toadstule/kumacub
    After=network-online.target
    Wants=network-online.target
    
    [Service]
    ExecStart=/root/.local/bin/uv run --isolated --no-progress --python=3.13 --with kumacub kumacubd
    ExecReload=/bin/kill -HUP $MAINPID
    
    [Install]
    WantedBy=multi-user.target   
    ```
3. Create a config file `/etc/kumacub/config.toml`:
    ```bash
    sudo mkdir /etc/kumacub
    ```
    ```toml
    [log]
    level = "DEBUG"
    structured = false
    
    [[checks]]
    name = "sampe check"
    executor.command = "echo"
    executor.args = ["-n", "OK - sample check is working"]
    publisher.url = "https://uptime-kuma.example.com"
    publisher.push_token = "your-push-token-here"
    schedule.interval = 60
    ```
4. Reload systemd daemon:
    ```bash
    sudo systemctl daemon-reload
    ```
5. Start the service:
    ```bash
    sudo systemctl start kumacubd
    ```

### Manual Installation (PIP)

We understand that this is a bit rough; it's a work in progress.

```bash
pip install kumacub
sudo mkdir /etc/kumacub
sudo mv /usr/local/config.toml /etc/kumacub/config.toml
sudo mv /usr/local/kumacubd.service /etc/systemd/system/
sudo sed -i 's|/usr/bin/kumacubd|/usr/local/bin/kumacubd|' /etc/systemd/system/kumacubd.service
sudo systemctl daemon-reload
```

## Configuration

KumaCub uses a TOML configuration file. By default, it looks for `/etc/kumacub/config.toml`, but you can override this with the `KUMACUB__CONFIG` environment variable.

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
- **publisher.url**: Uptime Kuma instance URL
- **publisher.push_token**: Uptime Kuma push token
- **schedule.interval**: Check interval in seconds (default: `60`)

### Environment Variables

You can override any configuration value using environment variables with the `KUMACUB__` prefix:

```bash
# Override config file location
export KUMACUB__CONFIG=/path/to/config.toml

# Override log level
export KUMACUB__LOG__LEVEL=DEBUG

# Override log format
export KUMACUB__LOG__STRUCTURED=false
```

## Usage

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

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.
