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
from agent import CarSearchAgent


class CarSearchAgentExecutor(AgentExecutor):
    """Car Search AgentExecutor following A2A protocol with proper structured data support."""

    def __init__(self):
        self.agent = CarSearchAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the car search agent following A2A protocol."""
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

                if not is_task_complete:
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            item["updates"], task.context_id, task.id
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

                # Create proper A2A response with artifacts
                if car_data and car_data.get("has_recommendation"):
                    # Create artifact with both text and data parts using TaskUpdater.add_artifact()
                    from a2a.types import Part, TextPart, DataPart

                    parts = [
                        # Conversational text part
                        Part(root=TextPart(text=str(content) if content else "")),
                        # Structured data part
                        Part(root=DataPart(data=car_data)),
                    ]

                    # Use TaskUpdater.add_artifact() method with only documented parameters
                    await updater.add_artifact(
                        parts=parts,
                        artifact_id=f"car_search_result_{task.id}",
                        name="Car Search Result",
                        metadata={"dataType": "car_recommendation"},
                    )

                    # Update the status to completed
                    await updater.update_status(
                        TaskState.completed,
                        final=True,
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
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"Car search failed: {str(e)}",
                    task.context_id,
                    task.id,
                ),
                final=True,
            )

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> None:
        """Cancel the current car search task."""
        raise ServerError(error=UnsupportedOperationError())
