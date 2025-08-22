# Agentic Orchestration Samples

This repository contains runnable examples demonstrating Rasa's advanced agentic
orchestration capabilities. These samples showcase how to build sophisticated
conversational AI systems that can coordinate multiple agents, integrate external
tools, and manage complex workflows through intelligent orchestration.

## What is Agentic Orchestration?

Agentic orchestration refers to the ability to coordinate multiple specialized AI
agents within a single conversational interface. This includes:
- **Multi-agent coordination**: Managing conversations across different specialized
  agents
- **Protocol integration**: Combining MCP (Model Context Protocol), A2A
  (Agent-to-Agent), and Rasa Flows
- **Context management**: Maintaining conversation state and context across different
  phases
- **Workflow orchestration**: Intelligent routing and decision-making between different
  conversation phases

## Available Samples

### 1. Appointment Booking Assistant
A demonstration of how to use an agent to intelligently fill appointment slots based
on user preferences and constraints. This sample showcases:
- **MCP Integration**: Using an MCP server for appointment scheduling capabilities
- **Direct Tool Integration**: Calling tools directly within Flows

📖 **[View README](appointment-booking-assistant/README.md)**

### 2. Car Purchase Assistant
A demonstration of advanced agentic orchestration for complex, multi-phase workflows.
This sample showcases:
- **MCP-Powered Research**: Uses an agent that leverages an MCP server to perform
  real-time car research and help users find suitable car models.
- **A2A-Powered Shopping**: Integrates an A2A (Agent-to-Agent) server to power a
  dedicated car shopping agent, enabling structured car searches, recommendations, and
  dealer connections.
- **End-to-End Workflow**: Guides users through research, shopping, and financing
  phases within a single conversational interface.
- **Context Management**: Maintains and transfers relevant information seamlessly
  across all phases of the car buying journey.

📖 **[View README](car-purchase-assistant/README.md)**

## Getting Started

Choose a sample that best fits your use case and follow its README for setup and usage
instructions.
