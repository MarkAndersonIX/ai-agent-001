#!/usr/bin/env python3

import click
import requests
import json
import sys
from typing import Optional, Dict, Any
from pathlib import Path
import uuid


class AgentCLI:
    """Command-line interface for AI Agent Base."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize CLI with API base URL."""
        self.base_url = base_url.rstrip("/")
        self.session_file = Path.home() / ".ai_agent_sessions.json"
        self.sessions = self._load_sessions()

    def _load_sessions(self) -> Dict[str, str]:
        """Load saved sessions from file."""
        try:
            if self.session_file.exists():
                with open(self.session_file, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_sessions(self) -> None:
        """Save sessions to file."""
        try:
            with open(self.session_file, "w") as f:
                json.dump(self.sessions, f, indent=2)
        except Exception:
            pass

    def _get_session_id(
        self, agent_type: str, session_name: Optional[str] = None
    ) -> str:
        """Get or create session ID."""
        key = f"{agent_type}:{session_name or 'default'}"

        if key not in self.sessions:
            self.sessions[key] = f"{agent_type}_{uuid.uuid4().hex[:8]}"
            self._save_sessions()

        return self.sessions[key]

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request to API."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            return response
        except requests.exceptions.ConnectionError:
            click.echo(
                f"Error: Could not connect to API server at {self.base_url}", err=True
            )
            click.echo(
                "Make sure the server is running with: python -m api.server", err=True
            )
            sys.exit(1)
        except requests.exceptions.Timeout:
            click.echo("Error: Request timed out", err=True)
            sys.exit(1)

    def health_check(self) -> bool:
        """Check if API server is healthy."""
        try:
            response = self._make_request("GET", "/health")
            return response.status_code == 200
        except:
            return False

    def list_agents(self) -> None:
        """List available agents."""
        response = self._make_request("GET", "/agents")

        if response.status_code == 200:
            data = response.json()
            agents = data.get("agents", {})

            click.echo("Available Agents:")
            click.echo("=================")

            for agent_type, info in agents.items():
                click.echo(f"\n{agent_type}:")
                click.echo(f"  Description: {info.get('system_prompt', '')[:100]}...")
                click.echo(f"  Tools: {', '.join(info.get('tools', []))}")
        else:
            click.echo(f"Error: {response.status_code} - {response.text}", err=True)

    def chat_with_agent(
        self,
        agent_type: str,
        message: str,
        session_name: Optional[str] = None,
        show_sources: bool = False,
    ) -> None:
        """Chat with an agent."""
        session_id = self._get_session_id(agent_type, session_name)

        response = self._make_request(
            "POST",
            f"/agents/{agent_type}/chat",
            json={"message": message, "session_id": session_id},
        )

        if response.status_code == 200:
            data = response.json()

            click.echo(f"\n{agent_type.title()} Agent:")
            click.echo("=" * (len(agent_type) + 7))
            click.echo(data["response"])

            if show_sources and data.get("sources"):
                click.echo("\nSources:")
                for i, source in enumerate(data["sources"], 1):
                    if "url" in source:
                        click.echo(f"  {i}. {source.get('title', 'Web Source')}")
                        click.echo(f"     {source['url']}")
                    else:
                        click.echo(
                            f"  {i}. {source.get('metadata', {}).get('title', 'Document')}"
                        )

            click.echo(f"\nSession: {session_id}")

        else:
            error_data = (
                response.json()
                if response.headers.get("content-type") == "application/json"
                else {}
            )
            error_msg = error_data.get("error", response.text)
            click.echo(f"Error: {response.status_code} - {error_msg}", err=True)

    def show_session_history(
        self, agent_type: str, session_name: Optional[str] = None
    ) -> None:
        """Show session conversation history."""
        session_id = self._get_session_id(agent_type, session_name)

        response = self._make_request(
            "GET", f"/agents/{agent_type}/sessions/{session_id}"
        )

        if response.status_code == 200:
            data = response.json()

            click.echo(f"\nSession History: {session_id}")
            click.echo("=" * (len(session_id) + 17))
            click.echo(f"Agent: {data['agent_type']}")
            click.echo(f"Created: {data['created_at']}")
            click.echo(f"Messages: {data['message_count']}")
            click.echo("")

            for msg in data.get("messages", []):
                role = msg["role"].title()
                content = msg["content"]
                timestamp = msg["timestamp"][:19].replace("T", " ")

                click.echo(f"[{timestamp}] {role}:")
                click.echo(f"  {content}")
                click.echo("")

        elif response.status_code == 404:
            click.echo("No conversation history found for this session.", err=True)
        else:
            click.echo(f"Error: {response.status_code} - {response.text}", err=True)

    def list_tools(self, agent_type: str) -> None:
        """List available tools for an agent."""
        response = self._make_request("GET", f"/agents/{agent_type}/tools")

        if response.status_code == 200:
            data = response.json()
            tools = data.get("tool_details", {})

            click.echo(f"\nTools for {agent_type} agent:")
            click.echo("=" * (len(agent_type) + 12))

            for tool_name, tool_info in tools.items():
                click.echo(f"\n{tool_name}:")
                click.echo(f"  Description: {tool_info['description']}")

                if tool_info.get("examples"):
                    click.echo("  Examples:")
                    for example in tool_info["examples"][:2]:  # Show first 2 examples
                        click.echo(f"    - {example}")
        else:
            click.echo(f"Error: {response.status_code} - {response.text}", err=True)

    def execute_tool(self, agent_type: str, tool_name: str, input_text: str) -> None:
        """Execute a tool directly."""
        response = self._make_request(
            "POST",
            f"/agents/{agent_type}/tools/{tool_name}",
            json={"input": input_text},
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("success"):
                click.echo(f"\nTool Result ({tool_name}):")
                click.echo("=" * (len(tool_name) + 14))
                click.echo(data["content"])

                if data.get("metadata"):
                    click.echo(f"\nMetadata: {data['metadata']}")
            else:
                click.echo(
                    f"Tool execution failed: {data.get('error', 'Unknown error')}",
                    err=True,
                )
        else:
            click.echo(f"Error: {response.status_code} - {response.text}", err=True)


# CLI Commands
@click.group()
@click.option("--api-url", default="http://localhost:8000", help="API server URL")
@click.pass_context
def cli(ctx, api_url):
    """AI Agent Base CLI - Command-line interface for interacting with AI agents."""
    ctx.ensure_object(dict)
    ctx.obj["client"] = AgentCLI(api_url)

    # Check if server is running
    if not ctx.obj["client"].health_check():
        click.echo(f"Warning: API server at {api_url} is not responding", err=True)
        click.echo("Start the server with: python -m api.server", err=True)


@cli.command()
@click.pass_context
def agents(ctx):
    """List available agents."""
    ctx.obj["client"].list_agents()


@cli.command()
@click.argument(
    "agent_type",
    type=click.Choice(["general", "code_assistant", "research_agent", "document_qa"]),
)
@click.argument("message")
@click.option("--session", "-s", help='Session name (default: "default")')
@click.option("--sources", is_flag=True, help="Show sources in response")
@click.pass_context
def chat(ctx, agent_type, message, session, sources):
    """Chat with an agent."""
    ctx.obj["client"].chat_with_agent(agent_type, message, session, sources)


@cli.command()
@click.argument(
    "agent_type",
    type=click.Choice(["general", "code_assistant", "research_agent", "document_qa"]),
)
@click.option("--session", "-s", help='Session name (default: "default")')
@click.pass_context
def history(ctx, agent_type, session):
    """Show conversation history for a session."""
    ctx.obj["client"].show_session_history(agent_type, session)


@cli.command()
@click.argument(
    "agent_type",
    type=click.Choice(["general", "code_assistant", "research_agent", "document_qa"]),
)
@click.pass_context
def tools(ctx, agent_type):
    """List available tools for an agent."""
    ctx.obj["client"].list_tools(agent_type)


@cli.command()
@click.argument(
    "agent_type",
    type=click.Choice(["general", "code_assistant", "research_agent", "document_qa"]),
)
@click.argument("tool_name")
@click.argument("input_text")
@click.pass_context
def tool(ctx, agent_type, tool_name, input_text):
    """Execute a tool directly."""
    ctx.obj["client"].execute_tool(agent_type, tool_name, input_text)


@cli.command()
@click.argument(
    "agent_type",
    type=click.Choice(["general", "code_assistant", "research_agent", "document_qa"]),
)
@click.option("--session", "-s", help='Session name (default: "default")')
@click.pass_context
def interactive(ctx, agent_type, session):
    """Start interactive chat session with an agent."""
    client = ctx.obj["client"]

    click.echo(f"Starting interactive session with {agent_type} agent")
    click.echo("Type 'quit' or 'exit' to end the session")
    click.echo("Type 'history' to see conversation history")
    click.echo("Type 'tools' to see available tools")
    click.echo("=" * 50)

    while True:
        try:
            message = click.prompt(f"\n[{agent_type}]", type=str)

            if message.lower() in ["quit", "exit"]:
                click.echo("Goodbye!")
                break
            elif message.lower() == "history":
                client.show_session_history(agent_type, session)
                continue
            elif message.lower() == "tools":
                client.list_tools(agent_type)
                continue

            client.chat_with_agent(agent_type, message, session, show_sources=True)

        except KeyboardInterrupt:
            click.echo("\nGoodbye!")
            break
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)


if __name__ == "__main__":
    cli()
