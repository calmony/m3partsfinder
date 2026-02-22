"""CLI entry point for the parts finder agent."""

import logging
import sys
import click
from pathlib import Path

from src.agent import Agent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """BMW E9X M3 Parts Finder Agent."""
    pass


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to config.yaml"
)
def search(config):
    """Run a single search cycle."""
    try:
        agent = Agent(config_path=config)
        agent.run_once()
        logger.info("Search cycle complete")
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to config.yaml"
)
def daemon(config):
    """Run continuously with scheduled searches."""
    try:
        click.echo("Starting parts finder daemon...")
        click.echo("Press Ctrl+C to stop.")
        agent = Agent(config_path=config)
        agent.run_scheduled()
    except KeyboardInterrupt:
        click.echo("\nDaemon stopped.")
    except Exception as e:
        logger.error(f"Daemon error: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind to (default: 127.0.0.1)"
)
@click.option(
    "--port",
    default=5000,
    type=int,
    help="Port to listen on (default: 5000)"
)
def web(host, port):
    """Launch the web dashboard."""
    try:
        from src.web import app
        click.echo(f"Starting web dashboard at http://{host}:{port}")
        click.echo("Press Ctrl+C to stop.")
        app.run(debug=False, host=host, port=port)
    except KeyboardInterrupt:
        click.echo("\nWeb server stopped.")
    except Exception as e:
        logger.error(f"Web server error: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to config.yaml"
)
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host for web app (default: 127.0.0.1)"
)
@click.option(
    "--port",
    default=5000,
    type=int,
    help="Port for web app (default: 5000)"
)
def all(config, host, port):
    """Run agent daemon AND web server (requires tmux or similar)."""
    click.echo("To run both daemon and web:")
    click.echo(f"  Terminal 1: python main.py daemon --config {config or 'src/config.yaml'}")
    click.echo(f"  Terminal 2: python main.py web --host {host} --port {port}")
    click.echo("\nOr use a process manager like supervisord or systemd.")


if __name__ == "__main__":
    cli()

