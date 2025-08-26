from rasa.agents.protocol.a2a.a2a_agent import A2AAgent
from rasa.agents.schemas import AgentOutput

from typing import List
from rasa.shared.core.events import SlotSet


class CarShoppingAgent(A2AAgent):
    async def process_output(self, output: AgentOutput) -> AgentOutput:
        """Post-process the output before returning it to Rasa."""
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
