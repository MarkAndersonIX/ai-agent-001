#!/usr/bin/env python3
"""
AI Agent Base - Main entry point

Usage:
    python -m ai_agent_base server    # Start API server
    python -m ai_agent_base cli       # Start CLI interface
    python -m ai_agent_base --help    # Show help
"""

import argparse
import sys
from pathlib import Path

# Add current directory to Python path for directory-based execution
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Main entry point for AI Agent Base."""
    parser = argparse.ArgumentParser(
        description="AI Agent Base - Extensible AI Agent Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m ai_agent_base server --port 8080
  python -m ai_agent_base cli chat general "Hello, how are you?"
  python -m ai_agent_base cli interactive code_assistant
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Server command
    server_parser = subparsers.add_parser("server", help="Start API server")
    server_parser.add_argument("--host", default=None, help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=None, help="Port to bind to")
    server_parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    server_parser.add_argument("--config", help="Path to additional config file")

    # CLI command
    cli_parser = subparsers.add_parser("cli", help="Start CLI interface")
    cli_parser.add_argument(
        "--api-url", default="http://localhost:8000", help="API server URL"
    )

    # Add CLI subcommands
    cli_subparsers = cli_parser.add_subparsers(dest="cli_command", help="CLI commands")

    # Chat command
    chat_parser = cli_subparsers.add_parser("chat", help="Chat with an agent")
    chat_parser.add_argument(
        "agent", choices=["general", "code_assistant", "research_agent", "document_qa"]
    )
    chat_parser.add_argument("message", help="Message to send to the agent")
    chat_parser.add_argument("--session", "-s", help="Session name")
    chat_parser.add_argument("--sources", action="store_true", help="Show sources")

    # Interactive command
    interactive_parser = cli_subparsers.add_parser(
        "interactive", help="Start interactive session"
    )
    interactive_parser.add_argument(
        "agent", choices=["general", "code_assistant", "research_agent", "document_qa"]
    )
    interactive_parser.add_argument("--session", "-s", help="Session name")

    # Agents command
    cli_subparsers.add_parser("agents", help="List available agents")

    # Tools command
    tools_parser = cli_subparsers.add_parser("tools", help="List tools for an agent")
    tools_parser.add_argument(
        "agent", choices=["general", "code_assistant", "research_agent", "document_qa"]
    )

    # History command
    history_parser = cli_subparsers.add_parser("history", help="Show session history")
    history_parser.add_argument(
        "agent", choices=["general", "code_assistant", "research_agent", "document_qa"]
    )
    history_parser.add_argument("--session", "-s", help="Session name")

    args = parser.parse_args()

    if args.command == "server":
        start_server(args)
    elif args.command == "cli":
        start_cli(args)
    else:
        parser.print_help()


def start_server(args):
    """Start the API server."""
    try:
        from api.server import create_app

        app = create_app(args.config)
        app.run(host=args.host, port=args.port, debug=args.debug)

    except ImportError as e:
        print(f"Error: Missing dependencies for server: {e}")
        print("Install with: pip install flask flask-cors")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


def start_cli(args):
    """Start the CLI interface."""
    try:
        from cli.main import AgentCLI

        client = AgentCLI(args.api_url)

        if args.cli_command == "chat":
            client.chat_with_agent(args.agent, args.message, args.session, args.sources)
        elif args.cli_command == "interactive":
            start_interactive_session(client, args.agent, args.session)
        elif args.cli_command == "agents":
            client.list_agents()
        elif args.cli_command == "tools":
            client.list_tools(args.agent)
        elif args.cli_command == "history":
            client.show_session_history(args.agent, args.session)
        else:
            # No subcommand, start interactive CLI
            print("AI Agent Base CLI")
            print("=================")
            print("Available commands:")
            print("  chat <agent> <message>    - Send a message to an agent")
            print("  interactive <agent>       - Start interactive session")
            print("  agents                    - List available agents")
            print("  tools <agent>             - List tools for an agent")
            print("  history <agent>           - Show session history")
            print("")
            print("Use --help with any command for more information")

    except ImportError as e:
        print(f"Error: Missing dependencies for CLI: {e}")
        print("Install with: pip install click requests")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting CLI: {e}")
        sys.exit(1)


def start_interactive_session(client, agent_type, session_name):
    """Start an interactive CLI session."""
    print(f"Starting interactive session with {agent_type} agent")
    print("Type 'quit' or 'exit' to end the session")
    print("Type 'history' to see conversation history")
    print("Type 'tools' to see available tools")
    print("=" * 50)

    while True:
        try:
            message = input(f"\n[{agent_type}] ")

            if message.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break
            elif message.lower() == "history":
                client.show_session_history(agent_type, session_name)
                continue
            elif message.lower() == "tools":
                client.list_tools(agent_type)
                continue

            client.chat_with_agent(agent_type, message, session_name, show_sources=True)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
