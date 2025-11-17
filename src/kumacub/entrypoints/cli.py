#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Console entrypoint KumaCub.

Usage:
    $ kumacub daemon      # Run the daemon (default)
    $ kumacub install     # Install service and config files
"""

from __future__ import annotations

import argparse
import asyncio
import os
import pathlib
import shutil
import subprocess
import sys
from importlib import resources

from kumacub import config
from kumacub.application.services import runner
from kumacub.application.services.daemon import KumaCubDaemon
from kumacub.infrastructure import executors, parsers, publishers
from kumacub.logging_config import configure_logging


class KumaCubCLI:
    """Command-line interface for KumaCub."""

    def main(self, args: list[str] | None = None) -> None:
        """Run the KumaCub CLI.

        Args:
            args: Command line arguments. If None, uses sys.argv[1:].
        """
        parsed_args = self._parse_args(args)

        if parsed_args.command == "install":
            self._install_files(
                config_dir=parsed_args.config_dir,
                systemd_dir=parsed_args.systemd_dir,
                force=parsed_args.force,
            )
        elif parsed_args.command == "daemon":
            KumaCubDaemon().run()
        else:
            self._run_checks()

    def _install_files(self, config_dir: pathlib.Path, systemd_dir: pathlib.Path, *, force: bool = False) -> None:
        """Install configuration and service files to system locations.

        Args:
            force: If True, overwrite existing files without prompting.
            config_dir: Directory to install config file to. Defaults to /etc/kumacub.
            systemd_dir: Directory to install systemd service file to. Defaults to /etc/systemd/system.
        """
        data_dir = resources.files("kumacub") / "data"
        config_src = data_dir / "config.toml"
        config_dest = config_dir / "config.toml"
        service_src = data_dir / "kumacub.service"
        service_dest = systemd_dir / "kumacub.service"

        for dir_ in (config_dir, systemd_dir):
            if not self._mkdir(dir_):
                msg = f"Error: Cannot write to directory: {dir_}; please try with sudo"
                raise SystemExit(msg)

        if config_dest.exists() and not force:
            msg = f"Config file {config_dest} already exists; use --force to overwrite"
            raise SystemExit(msg)
        if service_dest.exists() and not force:
            msg = f"Service file {service_dest} already exists; use --force to overwrite"
            raise SystemExit(msg)

        shutil.copy2(str(config_src), str(config_dest))
        print(f"Copied config to {config_dest}")

        # Write the systemd unit file (with the correct paths)
        service_content = service_src.read_text(encoding="utf-8")
        service_content = service_content.replace("/etc/kumacub/config.toml", str(config_dest))
        service_content = service_content.replace("/usr/bin/kumacub", str(self._get_script_path()))
        service_dest.write_text(service_content, encoding="utf-8")
        print(f"Created service file at {service_dest}")

        # Reload systemd if running as root
        if os.geteuid() == 0:
            print("Reloading systemd daemon...")
            try:
                subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=True)
                print("Systemd daemon reloaded successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to reload systemd daemon: {e}")
        else:
            print("\nNote: Run 'sudo systemctl daemon-reload' to load the new service file.")

        print("\nInstallation complete. Next steps:")
        print("1. Edit the config file if needed:")
        print(f"     sudo nano {config_dest}")
        print("2. Enable and start the service:")
        print("     sudo systemctl enable --now kumacub")

    @staticmethod
    def _get_script_path() -> pathlib.Path:
        """Get the path to the currently running script."""
        return pathlib.Path(sys.argv[0]).resolve()

    @staticmethod
    def _mkdir(directory: pathlib.Path) -> bool:
        """Check if a directory is writable, creating it if it doesn't exist."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return os.access(str(directory), os.W_OK)
        except (OSError, PermissionError):
            return False

    @staticmethod
    def _parse_args(args: list[str] | None = None) -> argparse.Namespace:
        """Parse command line arguments.

        Args:
            args: List of arguments to parse. If None, uses sys.argv[1:].
        """
        parser = argparse.ArgumentParser(
            description="KumaCub - Local checks for Uptime Kuma",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # Add subcommands
        subparsers = parser.add_subparsers(dest="command", required=False, help="Command to execute")

        # Daemon command (default)
        daemon_parser = subparsers.add_parser("daemon", help="Run the KumaCub daemon (default)")
        daemon_parser.set_defaults(func=lambda _args: None)  # No additional args needed

        # Install command
        install_parser = subparsers.add_parser("install", help="Install KumaCub service and configuration files")
        install_parser.add_argument(
            "--force", "-f", action="store_true", help="Overwrite existing files without prompting"
        )
        install_parser.add_argument(
            "--config-dir",
            type=pathlib.Path,
            default=pathlib.Path("/etc/kumacub"),
            help="Directory to install config file (default: /etc/kumacub)",
        )
        install_parser.add_argument(
            "--systemd-dir",
            type=pathlib.Path,
            default=pathlib.Path("/etc/systemd/system"),
            help="Directory to install systemd service file (default: /etc/systemd/system)",
        )

        return parser.parse_args(args)

    @staticmethod
    def _run_checks() -> None:
        """Run checks."""
        settings = config.get_settings()
        for check in settings.checks:
            check.publisher.name = "stdout"  # Print check results to stdout
            runner_ = runner.Runner(
                executor=executors.get_executor(check.executor.name),
                parser=parsers.get_parser(check.parser.name),
                publisher=publishers.get_publisher(check.publisher.name),
            )
            asyncio.run(runner_.run(check))


def main() -> None:
    """Entry point for the kumacub command."""
    settings = config.get_settings()
    configure_logging(level=settings.log.level, structured=settings.log.structured)

    cli = KumaCubCLI()
    cli.main()


if __name__ == "__main__":  # pragma: no cover
    main()
