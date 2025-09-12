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

        Example of structured_results:
        structured_results=[
          [{
            'name': 'shopping_agent_1',
            'result': {
              'final_reservation_decision': {
                'final_decision': 'reserve',
                'car_model': '2020 Audi Q3',
                'dealer_name': 'Premium Auto Center',
                'price': 23500
            },
          }]
        ]
        """
        tool_results = output.structured_results

        slot_events: List[SlotSet] = []

        if not tool_results:
            return output

        for index in range(len(tool_results)):
            iteration_results = tool_results[index]
            for result in iteration_results:
                if "result" in result and "final_reservation_decision" in result["result"]:

                    if result["result"]["final_reservation_decision"]["final_decision"] != "reserve":
                        break

                    for key, value in result["result"]["final_reservation_decision"].items():
                        if key == "car_model":
                            slot_events.append(SlotSet("car_model", value))
                        elif key == "price":
                            slot_events.append(SlotSet("car_price", value))
                        elif key == "dealer_name":
                            slot_events.append(SlotSet("dealer_name", value))

        # add the slot events to the output
        output.events = (
            slot_events if not output.events else output.events.extend(slot_events)
        )
        return output
