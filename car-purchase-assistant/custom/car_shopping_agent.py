from rasa.agents.protocol.a2a.a2a_agent import A2AAgent
from rasa.agents.schemas import AgentInput, AgentOutput

from typing import List
from rasa.agents.schemas.agent_input import AgentInputSlot
from rasa.shared.core.events import SlotSet


class CarShoppingAgent(A2AAgent):

    async def process_input(self, input: AgentInput) -> AgentInput:
        """Pre-process the input before sending it to Rasa."""
        slots_to_keep: List[AgentInputSlot] = []
        for slot in input.slots:
            if slot.name == "recommended_car_models":
                slots_to_keep.append(slot)
            if slot.name == "recommended_car_details":
                slots_to_keep.append(slot)

        input.slots = slots_to_keep
        return input

