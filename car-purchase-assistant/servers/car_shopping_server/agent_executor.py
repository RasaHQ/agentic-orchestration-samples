import json
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    TaskState,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError
from agent import CarShoppingAgent


class CarShoppingAgentExecutor(AgentExecutor):
    """Car Shopping AgentExecutor following A2A protocol with proper structured data support."""

    def __init__(self):
        self.agent = CarShoppingAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the car shopping agent following A2A protocol."""
        query = context.get_user_input()

        # Extract structured data from message parts
        structured_data = {}
        for part in context.message.parts:
            if hasattr(part.root, "data"):
                # This is a DataPart with structured data
                if isinstance(part.root.data, dict):
                    structured_data.update(part.root.data)

        task = context.current_task

        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            async for item in self.agent.stream(query, task.context_id, structured_data):
                is_task_complete = item["is_task_complete"]
                is_finalize_tool_called = item.get("finalize_tool_called")

                if not is_task_complete:
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            item["content"], task.context_id, task.id
                        ),
                    )
                    continue

                content = item["content"]
                session_id = item.get("session_id")

                # Get the session to check for structured data in state
                session = await self.agent._runner.session_service.get_session(
                    app_name=self.agent._agent.name,
                    user_id=self.agent._user_id,
                    session_id=session_id,
                )

                # Check for car recommendation data in session state
                car_data = (
                    session.state.get("current_car_recommendation") if session else None
                )
                similar_cars_data = (
                    session.state.get("similar_cars_recommendations") if session else None
                )
                dealer_data = (
                    session.state.get("dealer_recommendations") if session else None
                )
                final_decision_data = (
                    session.state.get("final_purchase_decision") if session else None
                )

                # Create proper A2A response with artifacts
                if is_finalize_tool_called:
                    # Final decision made - task is complete
                    from a2a.types import Part, TextPart, DataPart

                    # Create artifact with final decision data
                    parts = [
                        # Conversational text part
                        Part(root=TextPart(text=str(content) if content else "")),
                        # Structured data part with final decision
                        Part(root=DataPart(data={
                            "final_reservation_decision": final_decision_data,
                            "shopping_context": {
                                "query": query,
                                "task_complete": True,
                                "decision_type": final_decision_data.get("final_decision"),
                            }
                        })),
                    ]

                    # Use TaskUpdater.add_artifact() method
                    await updater.add_artifact(
                        parts=parts,
                        artifact_id=f"final_reservation_decision_{task.id}",
                        name="Final Reservation Decision",
                        metadata={
                            "dataType": "final_reservation_decision",
                            "decision": final_decision_data.get("final_decision"),
                            "car_model": final_decision_data.get("car_model"),
                            "dealer_name": final_decision_data.get("dealer_name"),
                            "price": final_decision_data.get("price"),
                        },
                    )

                    # Task is complete with final decision
                    await updater.update_status(
                        TaskState.completed,
                        new_agent_text_message(
                            str(content) if content else "", task.context_id, task.id
                        ),
                        final=True,
                    )
                elif similar_cars_data or dealer_data or car_data:
                    # Combine all relevant car shopping data
                    combined_data = {
                        "car_recommendation": car_data,
                        "similar_cars": similar_cars_data,
                        "dealer_recommendations": dealer_data,
                        "shopping_context": {
                            "query": query,
                            "has_availability": car_data and car_data.get("has_recommendation"),
                            "has_alternatives": similar_cars_data and similar_cars_data.get("has_alternatives"),
                            "has_dealer_info": dealer_data and dealer_data.get("has_dealer_recommendations"),
                        }
                    }

                    # Agent is presenting options and waiting for user decision
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(
                            str(content) if content else "", task.context_id, task.id
                        ),
                        final=True,
                        metadata=combined_data,
                    )
                else:
                    # Just text response if no car data
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(
                            str(content) if content else "", task.context_id, task.id
                        ),
                        final=True,
                    )
                break

        except Exception as e:
            print("*"*100)
            print(f"Error: {e}")
            print("*"*100)

            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"Car shopping failed: {str(e)}",
                    task.context_id,
                    task.id,
                ),
                final=True,
            )

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> None:
        """Cancel the current car shopping task."""
        raise ServerError(error=UnsupportedOperationError())
