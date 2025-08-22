# Agentic Orchestration Samples

This repository contains runnable examples demonstrating Rasa's advanced agentic
orchestration capabilities. These samples showcase how to build sophisticated
conversational AI systems that can coordinate multiple agents, integrate external
tools, and manage complex workflows through intelligent orchestration.

## What is Agentic Orchestration?

Agentic orchestration refers to the ability to coordinate multiple specialized AI
agents within a single conversational interface. This includes:
- **Multi-agent coordination**: Managing conversations across different specialized agents
- **Protocol integration**: Combining MCP (Model Context Protocol), A2A (Agent-to-Agent), and Rasa Flows
- **Context management**: Maintaining conversation state and context across different phases
- **Workflow orchestration**: Intelligent routing and decision-making between different conversation phases

## Available Samples

### 1. Appointment Booking Assistant
A demonstration of how to use an agent to intelligently fill appointment slots based
on user preferences and constraints. This sample showcases:
- **ReAct style sub agents in a flow**: Using an MCP server to build a specialized reAct style sub agent for letting the user freely give their preferences and letting them pick an available slot.
- **Direct Tool Integration**: Calling tools from an MCP server directly from Flows

📖 **[View README](appointment-booking-assistant/README.md)**


## Getting Started

Choose a sample that best fits your use case and follow its README for setup and usage instructions.
