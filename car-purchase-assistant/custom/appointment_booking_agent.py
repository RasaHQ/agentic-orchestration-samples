from ast import List
from rasa.agents.protocol.mcp.mcp_task_agent import MCPTaskAgent
from rasa.agents.schemas import (
    AgentInput,
)
from rasa.agents.schemas.agent_input import AgentInputSlot
from datetime import datetime
from rasa.shared.core.events import SlotSet


class AppointmentBookingAgent(MCPTaskAgent):

    async def process_input(self, input: AgentInput) -> AgentInput:
        """Pre-process the input before sending it to Rasa."""
        slots_to_keep: List[AgentInputSlot] = []
        for slot in input.slots:
            if slot.name == "dealer_name":
                slots_to_keep.append(slot)
            if slot.name == "car_model":
                slots_to_keep.append(slot)
        input.slots = slots_to_keep

        date_slot = AgentInputSlot(
            name="current_date_time",
            value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="datetime"
        )
        input.slots.append(date_slot)

        return input
