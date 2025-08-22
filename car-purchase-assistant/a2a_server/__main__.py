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
from agent import CarSearchAgent
from agent_executor import CarSearchAgentExecutor
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

        # Car Search Agent Configuration
        skill = AgentSkill(
            id="search_cars",
            name="Car Search Tool",
            description="Helps users find cars based on their preferences including car type, price range, and new/used preference.",
            tags=["car_search", "automotive", "shopping"],
            examples=[
                "I'm looking for a new compact SUV between $25,000 and $30,000",
                "Find me a used sedan under $25,000",
                "I want to buy a car",
                "Show me electric vehicles in my price range",
            ],
        )

        agent_card = AgentCard(
            name="Car Search Agent",
            description="This agent helps users find cars based on their preferences including car type, price range, and whether they want new or used vehicles.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=CarSearchAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=CarSearchAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        request_handler = DefaultRequestHandler(
            agent_executor=CarSearchAgentExecutor(),
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
        logger.error(f"Error importing car search modules: {e}")
        logger.error(
            "Make sure you have created the car_search_agent.py and car_search_executor.py files"
        )
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
