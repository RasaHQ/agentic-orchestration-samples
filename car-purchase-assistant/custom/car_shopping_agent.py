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

    async def process_output(self, output: AgentOutput) -> AgentOutput:
        """Post-process the output before returning it to Rasa.

        Example of tool_results:
        tool_results=[
          [{
            'tool_name': 'shopping_agent_1',
            'result': {
              'car_model': '2024 Honda CR-V',
              'price': 33000,
              'dealer': 'Honda Dealership',
              'car_type': 'SUV'
            }
          }]
        ]
        """
        tool_results = output.tool_results
        slot_events: List[SlotSet] = []

        if not tool_results:
            return output

        for index in range(len(tool_results)):
            iteration_results = tool_results[index]
            for result in iteration_results:
                if "result" in result:
                    for key, value in result["result"].items():
                        if key == "car_model":
                            slot_events.append(SlotSet("car_model", value))
                        elif key == "price":
                            slot_events.append(SlotSet("car_price", value))
                        elif key == "dealer":
                            slot_events.append(SlotSet("dealer_name", value))
                            slot_events.append(SlotSet("dealer_found", True))

        # add the slot events to the output
        output.events = (
            slot_events if not output.events else output.events.extend(slot_events)
        )
        return output
