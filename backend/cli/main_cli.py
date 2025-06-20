import argparse
import requests
from rich.console import Console
from pathlib import Path

console = Console()

API_URL = "http://localhost:8000/analyze/"  # Adjust if deployed elsewhere

def analyze(file_path: str, version: str):
    """
    Analyze Kubernetes YAML for deprecated APIs and suggest upgrades using AI.
    """
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        console.print(f"[bold red]Error:[/bold red] File '{file_path}' not found.")
        return

    with file_path_obj.open("rb") as f:
        files = {"file": (file_path_obj.name, f)}
        data = {"version": version}
        try:
            console.print(f"[blue]Uploading and analyzing file '{file_path_obj.name}' for version {version}...[/blue]")
            response = requests.post(API_URL, files=files, data=data)
        except requests.exceptions.ConnectionError:
            console.print("[red]Cannot connect to backend. Is the FastAPI server running?[/red]")
            return

    if response.status_code != 200:
        console.print(f"[red]Error from server:[/red] {response.text}")
        return

    result = response.json()
    console.rule("[bold green]🧪 Pluto Output[/bold green]")
    console.print(result["pluto_output"], style="cyan")

    console.rule("[bold green]🤖 AI Suggestions[/bold green]")
    console.print(result["ai_response"], style="magenta")

def main():
    parser = argparse.ArgumentParser(description="Analyze Kubernetes YAML for deprecated APIs and suggest upgrades using AI.")
    parser.add_argument("file", help="Path to kubeconfig or YAML file")
    parser.add_argument("--version", "-v", required=True, help="Target Kubernetes version")
    
    args = parser.parse_args()
    analyze(args.file, args.version)

if __name__ == "__main__":
    main()
