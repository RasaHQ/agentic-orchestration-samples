## MCP Server Capabilities

The MCP server (`mcp_server/appointment_server_http.py`) provides a powerful appointment scheduling tool that can:

### Core Functionality
- **Query Available Appointments**: Find up to 10 available appointment slots based on user preferences
- **Flexible Scheduling**: Handle various date and time constraints with intelligent defaults
- **Smart Availability**: Automatically exclude weekends and non-business hours (8 AM - 6 PM)
- **Doctor Preferences**: Support for preferred doctor selection or any available doctor

### Appointment Slot Generation
- **Business Hours**: Automatically respects standard business hours (8 AM - 6 PM)
- **Appointment Duration**: 30-minute appointment slots
- **Time Rounding**: Slots are rounded to common appointment times (00, 15, 30, 45 minutes)
- **Conflict Avoidance**: Automatically excludes user-specified non-available dates

### Input Flexibility
- **Date Formats**: Accepts dates in dd/mm/yyyy format
- **Time Formats**: Accepts times in HH:MM (24-hour) format
- **Default Values**: Uses "any" keyword for unspecified preferences with sensible defaults:
  - Start date: Today (if not specified)
  - End date: 2 weeks from start date (if not specified)
  - Start time: 9:00 AM (if not specified)
  - End time: 5:00 PM (if not specified)

### Technical Features
- **FastMCP Implementation**: Built using the FastMCP library for optimal performance
- **HTTP Transport**: Runs on http://localhost:8000/mcp for easy integration
- **JSON Responses**: Returns structured JSON with success/error handling
- **Error Handling**: Comprehensive error handling for invalid date/time formats
- **Realistic Constraints**: Generates realistic appointment slots considering business rules
