from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class JiraTicket:
    """Represents a JIRA ticket."""

    ticket_id: str
    summary: str
    description: str
    status: str
    priority: str
    assignee: str = ""
    labels: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)


class JiraClient(ABC):
    """Abstract JIRA client interface."""

    @abstractmethod
    def get_ticket(self, ticket_id: str) -> JiraTicket:
        ...

    @abstractmethod
    def add_comment(self, ticket_id: str, comment: str) -> None:
        ...

    @abstractmethod
    def list_tickets(self, project: str, status: str | None = None) -> list[JiraTicket]:
        ...


class MockJiraClient(JiraClient):
    """Mock JIRA client with sample flow cytometer tickets."""

    def __init__(self) -> None:
        self._tickets: dict[str, JiraTicket] = {
            "CYTO-101": JiraTicket(
                ticket_id="CYTO-101",
                summary="Laser power fluctuation during long acquisitions",
                description=(
                    "After 30 minutes of continuous acquisition at 488nm, "
                    "laser power drops by ~5%. This causes inconsistent "
                    "fluorescence intensity across the run. Need to investigate "
                    "thermal management of the laser module."
                ),
                status="Open",
                priority="High",
                assignee="firmware_team",
                labels=["laser", "stability", "hardware"],
            ),
            "CYTO-102": JiraTicket(
                ticket_id="CYTO-102",
                summary="Refactor PMT voltage calibration routine",
                description=(
                    "Current calibration routine is monolithic and hard to test. "
                    "Need to extract voltage sweep, peak detection, and gain "
                    "optimization into separate modules."
                ),
                status="Open",
                priority="Medium",
                assignee="software_team",
                labels=["refactor", "calibration", "pmt"],
            ),
            "CYTO-103": JiraTicket(
                ticket_id="CYTO-103",
                summary="Add flow rate feedback control",
                description=(
                    "Implement closed-loop control for sample flow rate using "
                    "the pressure sensor feedback. Target: maintain flow rate "
                    "within +/-2% of setpoint."
                ),
                status="In Progress",
                priority="High",
                assignee="firmware_team",
                labels=["fluidics", "control-loop", "feature"],
            ),
        }

    def get_ticket(self, ticket_id: str) -> JiraTicket:
        if ticket_id not in self._tickets:
            raise KeyError(f"Ticket not found: {ticket_id}")
        return self._tickets[ticket_id]

    def add_comment(self, ticket_id: str, comment: str) -> None:
        if ticket_id not in self._tickets:
            raise KeyError(f"Ticket not found: {ticket_id}")
        self._tickets[ticket_id].comments.append(comment)

    def list_tickets(self, project: str, status: str | None = None) -> list[JiraTicket]:
        tickets = [t for t in self._tickets.values() if t.ticket_id.startswith(project)]
        if status:
            tickets = [t for t in tickets if t.status == status]
        return tickets
