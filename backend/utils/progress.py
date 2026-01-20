import threading
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from rich.console import Console
from rich.live import Live
from rich.style import Style
from rich.table import Table
from rich.text import Text

console = Console()


class AgentProgress:
    """Manages progress tracking for multiple agents."""

    def __init__(self):
        self.agent_status: Dict[str, Dict[str, str]] = {}
        self.table = Table(show_header=False, box=None, padding=(0, 1))
        # Disable Live display for web/background contexts
        self.live = None 
        self.started = False
        self.update_handlers: List[Callable] = []
        self._lock = threading.Lock()

    def register_handler(self, handler: Callable):
        """Register a handler to be called when agent status updates."""
        with self._lock:
            if handler not in self.update_handlers:
                self.update_handlers.append(handler)
        return handler 

    def unregister_handler(self, handler: Callable):
        """Unregister a previously registered handler."""
        with self._lock:
            if handler in self.update_handlers:
                self.update_handlers.remove(handler)

    def start(self):
        """No-op for web service."""
        pass

    def stop(self):
        """No-op for web service."""
        pass

    def update_status(self, agent_name: str, ticker: Optional[str] = None, status: str = "", analysis: Optional[str] = None):
        """Update the status of an agent."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        with self._lock:
            if agent_name not in self.agent_status:
                self.agent_status[agent_name] = {"status": "", "ticker": None}

            if ticker:
                self.agent_status[agent_name]["ticker"] = ticker
            if status:
                self.agent_status[agent_name]["status"] = status
            if analysis:
                self.agent_status[agent_name]["analysis"] = analysis

            self.agent_status[agent_name]["timestamp"] = timestamp
            handlers = list(self.update_handlers)

        # Notify all registered handlers 
        for handler in handlers:
            try:
                handler(agent_name, ticker, status, analysis, timestamp)
            except Exception as e:
                print(f"Error in progress handler: {e}")

    def get_all_status(self):
        with self._lock:
            return {agent_name: {"ticker": info.get("ticker"), "status": info.get("status"), "display_name": self._get_display_name(agent_name)} for agent_name, info in self.agent_status.items()}

    def _get_display_name(self, agent_name: str) -> str:
        """Convert agent_name to a display-friendly format."""
        return agent_name.replace("_agent", "").replace("_", " ").title()

    def _refresh_display(self):
        """Refresh the progress display."""
        with self._lock:
            try:
                self.table.columns.clear()
                self.table.add_column(width=100)

                # Sort agents with Risk Management and Portfolio Management at the bottom
                def sort_key(item):
                    agent_name = item[0]
                    if "risk_management" in agent_name:
                        return (2, agent_name)
                    elif "portfolio_management" in agent_name:
                        return (3, agent_name)
                    else:
                        return (1, agent_name)

                for agent_name, info in sorted(self.agent_status.items(), key=sort_key):
                    status = info.get("status", "")
                    ticker = info.get("ticker")
                    # Create the status text with appropriate styling
                    if status.lower() == "done":
                        style = Style(color="green", bold=True)
                        symbol = "✓"
                    elif status.lower() == "error":
                        style = Style(color="red", bold=True)
                        symbol = "✗"
                    else:
                        style = Style(color="yellow")
                        symbol = "⋯"

                    agent_display = self._get_display_name(agent_name)
                    status_text = Text()
                    status_text.append(f"{symbol} ", style=style)
                    status_text.append(f"{agent_display:<20}", style=Style(bold=True))

                    if ticker:
                        status_text.append(f"[{ticker}] ", style=Style(color="cyan"))
                    status_text.append(status, style=style)

                    self.table.add_row(status_text)
            except Exception:
                pass


# Create a global instance
progress = AgentProgress()
