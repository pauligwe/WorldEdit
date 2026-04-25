import asyncio
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class AgentStatus:
    agent: str
    state: Literal["running", "done", "error"]
    message: str = ""
    data: dict = field(default_factory=dict)


class StatusBus:
    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[AgentStatus]]] = {}

    def subscribe(self, world_id: str) -> asyncio.Queue[AgentStatus]:
        q: asyncio.Queue[AgentStatus] = asyncio.Queue()
        self._queues.setdefault(world_id, []).append(q)
        return q

    def unsubscribe(self, world_id: str, q: asyncio.Queue[AgentStatus]) -> None:
        if world_id in self._queues and q in self._queues[world_id]:
            self._queues[world_id].remove(q)
            if not self._queues[world_id]:
                del self._queues[world_id]

    async def publish(self, world_id: str, evt: AgentStatus) -> None:
        for q in self._queues.get(world_id, []):
            await q.put(evt)
