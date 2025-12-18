"""Main CLI application for AI Platform."""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from . import __version__
from .client import APIClient, APIError
from .config import Config, get_config_path, load_config, save_config

app = typer.Typer(
    name="ai-platform",
    help="CLI for AI Development Platform - Manage deployments, RAG, and more.",
    add_completion=False,
)

console = Console()

# Sub-command groups
deployments_app = typer.Typer(help="Manage AI model deployments")
rag_app = typer.Typer(help="Manage RAG collections and documents")
config_app = typer.Typer(help="Manage CLI configuration")
analytics_app = typer.Typer(help="View analytics and usage")

app.add_typer(deployments_app, name="deployments")
app.add_typer(rag_app, name="rag")
app.add_typer(config_app, name="config")
app.add_typer(analytics_app, name="analytics")


def handle_error(e: Exception) -> None:
    """Handle and display errors."""
    console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(1)


def print_json(data: dict | list) -> None:
    """Print data as formatted JSON."""
    console.print_json(json.dumps(data, indent=2, default=str))


# ============== Main Commands ==============

@app.command()
def version():
    """Show CLI version."""
    console.print(f"AI Platform CLI v{__version__}")


@app.command()
def login(
    email: str = typer.Option(..., prompt=True, help="Your email address"),
    password: str = typer.Option(
        ..., prompt=True, hide_input=True, help="Your password"
    ),
):
    """Login to AI Platform and save credentials."""
    try:
        with APIClient() as client:
            result = client.login(email, password)

            # Save the token to config
            config = load_config()
            config.api_key = result["access_token"]
            save_config(config)

            console.print("[green]✓[/green] Successfully logged in!")
            console.print(f"Token saved to {get_config_path()}")
    except APIError as e:
        handle_error(e)


@app.command()
def status():
    """Check API connection status."""
    try:
        with APIClient() as client:
            result = client.health_check()

            table = Table(title="API Status")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Status", result.get("status", "unknown"))
            table.add_row("Database", result.get("database", "unknown"))
            table.add_row("Redis", result.get("redis", "unknown"))
            table.add_row("Version", result.get("version", "unknown"))

            console.print(table)
    except APIError as e:
        handle_error(e)


# ============== Deployments Commands ==============

@deployments_app.command("list")
def list_deployments(
    output: str = typer.Option("table", help="Output format: table, json"),
):
    """List all deployments."""
    try:
        with APIClient() as client:
            deployments = client.list_deployments()

            if output == "json":
                print_json(deployments)
                return

            if not deployments:
                console.print("[yellow]No deployments found.[/yellow]")
                return

            table = Table(title="Deployments")
            table.add_column("ID", style="dim")
            table.add_column("Name", style="cyan")
            table.add_column("Model", style="magenta")
            table.add_column("Status", style="green")
            table.add_column("Max Tokens")
            table.add_column("Temperature")

            for d in deployments:
                status_style = {
                    "running": "green",
                    "stopped": "yellow",
                    "error": "red",
                    "deploying": "blue",
                }.get(d["status"], "white")

                table.add_row(
                    d["id"][:8],
                    d["name"],
                    d["model_name"],
                    f"[{status_style}]{d['status']}[/{status_style}]",
                    str(d.get("max_tokens", "N/A")),
                    str(d.get("temperature", "N/A")),
                )

            console.print(table)
    except APIError as e:
        handle_error(e)


@deployments_app.command("create")
def create_deployment(
    name: str = typer.Option(..., help="Deployment name"),
    model: str = typer.Option("gpt-4", help="Model name"),
    max_tokens: int = typer.Option(4096, help="Maximum tokens"),
    temperature: float = typer.Option(0.7, help="Temperature"),
):
    """Create a new deployment."""
    try:
        with APIClient() as client:
            result = client.create_deployment(
                name=name,
                model_name=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            console.print("[green]✓[/green] Deployment created successfully!")
            console.print(f"  ID: {result['id']}")
            console.print(f"  Name: {result['name']}")
            console.print(f"  Model: {result['model_name']}")
    except APIError as e:
        handle_error(e)


@deployments_app.command("delete")
def delete_deployment(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a deployment."""
    if not force:
        confirm = typer.confirm(
            f"Are you sure you want to delete deployment {deployment_id}?")
        if not confirm:
            raise typer.Abort()

    try:
        with APIClient() as client:
            client.delete_deployment(deployment_id)
            console.print("[green]✓[/green] Deployment deleted successfully!")
    except APIError as e:
        handle_error(e)


@deployments_app.command("start")
def start_deployment(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
):
    """Start a deployment."""
    try:
        with APIClient() as client:
            client.start_deployment(deployment_id)
            console.print("[green]✓[/green] Deployment started!")
    except APIError as e:
        handle_error(e)


@deployments_app.command("stop")
def stop_deployment(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
):
    """Stop a deployment."""
    try:
        with APIClient() as client:
            client.stop_deployment(deployment_id)
            console.print("[green]✓[/green] Deployment stopped!")
    except APIError as e:
        handle_error(e)


@deployments_app.command("invoke")
def invoke_deployment(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="Prompt to send"),
):
    """Invoke a deployment with a prompt."""
    try:
        with APIClient() as client:
            with console.status("[bold green]Generating response..."):
                result = client.invoke_deployment(deployment_id, prompt)

            console.print(Panel(result.get("response", ""), title="Response"))

            if "usage" in result:
                console.print(
                    f"\n[dim]Tokens: {result['usage'].get('total_tokens', 'N/A')}[/dim]")
    except APIError as e:
        handle_error(e)


# ============== RAG Commands ==============

@rag_app.command("collections")
def list_collections(
    output: str = typer.Option("table", help="Output format: table, json"),
):
    """List all RAG collections."""
    try:
        with APIClient() as client:
            collections = client.list_collections()

            if output == "json":
                print_json(collections)
                return

            if not collections:
                console.print("[yellow]No collections found.[/yellow]")
                return

            table = Table(title="RAG Collections")
            table.add_column("ID", style="dim")
            table.add_column("Name", style="cyan")
            table.add_column("Description")
            table.add_column("Documents", justify="right")

            for c in collections:
                table.add_row(
                    c["id"][:8],
                    c["name"],
                    c.get("description", "")[:50],
                    str(c.get("document_count", 0)),
                )

            console.print(table)
    except APIError as e:
        handle_error(e)


@rag_app.command("create")
def create_collection(
    name: str = typer.Option(..., help="Collection name"),
    description: str = typer.Option("", help="Collection description"),
):
    """Create a new RAG collection."""
    try:
        with APIClient() as client:
            result = client.create_collection(
                name=name, description=description)

            console.print("[green]✓[/green] Collection created successfully!")
            console.print(f"  ID: {result['id']}")
            console.print(f"  Name: {result['name']}")
    except APIError as e:
        handle_error(e)


@rag_app.command("upload")
def upload_document(
    collection_id: str = typer.Option(...,
                                      "--collection", "-c", help="Collection ID"),
    file_path: str = typer.Argument(..., help="Path to file to upload"),
):
    """Upload a document to a RAG collection."""
    try:
        with APIClient() as client:
            with console.status(f"[bold green]Uploading {file_path}..."):
                result = client.upload_document(collection_id, file_path)

            console.print("[green]✓[/green] Document uploaded successfully!")
            console.print(f"  Document ID: {result['id']}")
            console.print(f"  Status: {result['status']}")
    except APIError as e:
        handle_error(e)


@rag_app.command("query")
def query_collection(
    collection_id: str = typer.Option(...,
                                      "--collection", "-c", help="Collection ID"),
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    top_k: int = typer.Option(5, help="Number of results"),
):
    """Query a RAG collection."""
    try:
        with APIClient() as client:
            with console.status("[bold green]Searching..."):
                result = client.query_collection(collection_id, query, top_k)

            results = result.get("results", [])

            if not results:
                console.print("[yellow]No results found.[/yellow]")
                return

            console.print(f"\n[bold]Found {len(results)} results:[/bold]\n")

            for i, r in enumerate(results, 1):
                score = r.get("score", 0) * 100
                console.print(Panel(
                    r.get("text", ""),
                    title=f"[{i}] Score: {score:.1f}%",
                    subtitle=r.get("metadata", {}).get("source", ""),
                ))
    except APIError as e:
        handle_error(e)


# ============== Analytics Commands ==============

@analytics_app.command("dashboard")
def show_dashboard():
    """Show dashboard analytics."""
    try:
        with APIClient() as client:
            data = client.get_dashboard()

            table = Table(title="Dashboard Overview")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")

            table.add_row("Total Deployments", str(
                data.get("total_deployments", 0)))
            table.add_row("Active Deployments", str(
                data.get("active_deployments", 0)))
            table.add_row("Total Requests",
                          f"{data.get('total_requests', 0):,}")
            table.add_row("Total Cost", f"${data.get('total_cost', 0):.2f}")

            console.print(table)
    except APIError as e:
        handle_error(e)


@analytics_app.command("usage")
def show_usage(
    period: str = typer.Option("7d", help="Period: 24h, 7d, 30d, 90d"),
    output: str = typer.Option("table", help="Output format: table, json"),
):
    """Show usage analytics."""
    try:
        with APIClient() as client:
            data = client.get_usage(period)

            if output == "json":
                print_json(data)
                return

            console.print(f"\n[bold]Usage for last {period}:[/bold]\n")
            console.print(
                f"  Total Requests: {data.get('total_requests', 0):,}")
            console.print(f"  Total Tokens: {data.get('total_tokens', 0):,}")
            console.print(
                f"  Avg Response Time: {data.get('avg_response_time', 0):.0f}ms")
    except APIError as e:
        handle_error(e)


@analytics_app.command("costs")
def show_costs(
    period: str = typer.Option("7d", help="Period: 24h, 7d, 30d, 90d"),
    output: str = typer.Option("table", help="Output format: table, json"),
):
    """Show cost analytics."""
    try:
        with APIClient() as client:
            data = client.get_costs(period)

            if output == "json":
                print_json(data)
                return

            console.print(f"\n[bold]Costs for last {period}:[/bold]\n")
            console.print(f"  Total Cost: ${data.get('total_cost', 0):.2f}")

            model_costs = data.get("model_costs", [])
            if model_costs:
                console.print("\n  [bold]By Model:[/bold]")
                for m in model_costs:
                    console.print(f"    {m['model']}: ${m['cost']:.2f}")
    except APIError as e:
        handle_error(e)


# ============== Config Commands ==============

@config_app.command("show")
def show_config():
    """Show current configuration."""
    config = load_config()

    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("API URL", config.api_url)
    table.add_row("API Key", "***" if config.api_key else "[red]Not set[/red]")
    table.add_row("Default Model", config.default_model)
    table.add_row("Output Format", config.output_format)
    table.add_row("Config File", str(get_config_path()))

    console.print(table)


@config_app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value"),
):
    """Set a configuration value."""
    config = load_config()

    if key == "api_url":
        config.api_url = value
    elif key == "api_key":
        config.api_key = value
    elif key == "default_model":
        config.default_model = value
    elif key == "output_format":
        if value not in ["table", "json", "yaml"]:
            console.print(
                "[red]Invalid output format. Use: table, json, yaml[/red]")
            raise typer.Exit(1)
        config.output_format = value
    else:
        console.print(f"[red]Unknown configuration key: {key}[/red]")
        raise typer.Exit(1)

    save_config(config)
    console.print(f"[green]✓[/green] Set {key} = {value}")


@config_app.command("path")
def show_config_path():
    """Show configuration file path."""
    console.print(str(get_config_path()))


if __name__ == "__main__":
    app()
