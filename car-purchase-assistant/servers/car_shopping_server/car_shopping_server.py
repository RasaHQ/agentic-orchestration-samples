import logging
import os
import click
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent import CarShoppingAgent
from agent_executor import CarShoppingAgentExecutor
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""

    pass


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10002)
def main(host, port):
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "TRUE":
            if not os.getenv("GOOGLE_API_KEY"):
                raise MissingAPIKeyError(
                    "GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
                )

        capabilities = AgentCapabilities(streaming=True)

        # Car Shopping Agent Configuration
        skill = AgentSkill(
            id="car_shopping",
            name="Car Shopping Tool",
            description="Helps users check car availability at specific dealers, find similar cars when exact models aren't available, get dealer recommendations, and reserve cars.",
            tags=["car_shopping", "automotive", "dealer", "availability", "reservation"],
            examples=[
                "Do you have a 2024 Hyundai Tucson at Hyundai Motors?",
                "I want a Honda CR-V - which dealers have it?",
                "Is there a new Camry at Toyota Center?",
                "I'm looking for a compact SUV at VW Autohaus",
                "Find me a used BMW 3 Series",
                "I'd like to reserve the 2024 Toyota Camry at Auto City Motors",
            ],
        )

        agent_card = AgentCard(
            name="Car Shopping Agent",
            description="This agent helps users find specific cars at dealers, check availability, provides recommendations for similar cars when the exact model isn't available, and helps users reserve cars.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=CarShoppingAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=CarShoppingAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        request_handler = DefaultRequestHandler(
            agent_executor=CarShoppingAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )

        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        logger.info(f"Agent: {agent_card.name}")
        logger.info(f"Server starting on http://{host}:{port}")

        import uvicorn

        uvicorn.run(server.build(), host=host, port=port)

    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except ImportError as e:
        logger.error(f"Error importing car shopping modules: {e}")
        logger.error(
            "Make sure you have created the agent.py and agent_executor.py files"
        )
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
