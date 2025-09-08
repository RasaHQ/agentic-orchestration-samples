#!/usr/bin/env python3
"""
MCP Server for Appointment Booking using FastMCP
Provides a tool to query available appointment slots based on user preferences.
Much simpler implementation using FastMCP library.
"""

import json
from datetime import datetime, timedelta, date
import random
from typing import Any, Dict, List, Optional, Union

from fastmcp import FastMCP


# Create FastMCP server
mcp = FastMCP("Appointment Booking Server")


def generate_appointment_slots(
    start_date: datetime,
    end_date: datetime,
    start_hour: int,
    start_minute: int,
    end_hour: int,
    end_minute: int,
    preferred_doctor: str,
    excluded_dates: List[date],
) -> List[str]:
    """Generate up to 10 realistic appointment slots within the given constraints,
    excluding user's non-available days"""

    slots: List[str] = []
    current_date: datetime = start_date
    max_slots: int = 10

    # Define typical appointment duration (30 minutes)
    appointment_duration: timedelta = timedelta(minutes=30)

    # Ensure we don't generate appointments outside business hours (8 AM - 6 PM)
    business_start: int = max(start_hour, 8)
    business_end: int = min(end_hour, 18)

    # If the time range doesn't overlap with business hours, adjust
    if business_start >= business_end:
        business_start = 9
        business_end = 17

    attempts: int = 0
    max_attempts: int = 50  # Prevent infinite loops

    while (
        len(slots) < max_slots and current_date <= end_date and attempts < max_attempts
    ):
        attempts += 1

        # Check if current date is in user's non-available days
        if current_date.date() in excluded_dates:
            current_date += timedelta(days=1)
            continue

        # Skip weekends for realistic doctor appointments
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            # Generate random hour and minute within business hours
            random_hour: int = random.randint(business_start, business_end - 1)

            # Round minutes to common appointment times (00, 15, 30, 45)
            random_minute: int = random.choice([0, 15, 30, 45])

            # Ensure the appointment fits within user's time preferences
            appointment_time: datetime = current_date.replace(
                hour=random_hour, minute=random_minute, second=0, microsecond=0
            )

            # Check if appointment time is within user's daily availability
            user_start_time: datetime = current_date.replace(hour=start_hour, minute=start_minute)
            user_end_time: datetime = current_date.replace(hour=end_hour, minute=end_minute)

            if (
                user_start_time
                <= appointment_time
                <= (user_end_time - appointment_duration)
            ):
                # Format: dd/mm/yyyy ; HH:MM
                formatted_slot: str = appointment_time.strftime("%d/%m/%Y ; %H:%M")

                # Avoid duplicate slots
                if formatted_slot not in slots:
                    slots.append(formatted_slot)

        # Move to next day
        current_date += timedelta(days=1)

    # If we couldn't generate enough slots within the date range,
    # try to generate more within the first few days
    if len(slots) < max_slots and len(slots) > 0:
        # Try to fill remaining slots from the first available days
        for i in range(max_slots - len(slots)):
            additional_date: datetime = start_date + timedelta(days=i + 1)

            # Skip if date is excluded or weekend
            if (
                additional_date.date() in excluded_dates
                or additional_date.weekday() >= 5
                or additional_date > end_date
            ):
                continue

            additional_hour: int = random.randint(business_start, business_end - 1)
            additional_minute: int = random.choice([0, 15, 30, 45])

            additional_time: datetime = additional_date.replace(
                hour=additional_hour, minute=additional_minute
            )

            formatted_slot: str = additional_time.strftime("%d/%m/%Y ; %H:%M")
            if formatted_slot not in slots:
                slots.append(formatted_slot)

    return slots[:max_slots]  # Ensure we return at most 10 slots


@mcp.tool()
def query_available_appointments(
    user_availability_start_date: str,
    user_availability_end_date: str,
    user_availability_start_time: str,
    user_availability_end_time: str,
    preferred_doctor: str,
    non_available_days: str,
) -> Dict[str, Any]:
    """
    Query available appointment slots based on user preferences.
    Returns up to 10 available appointment slots within the specified criteria.
    Handles 'any' values by providing sensible defaults.

    Args:
        user_availability_start_date: Start date for availability in dd/mm/yyyy format. Use 'any' if not specified.
        user_availability_end_date: End date for availability in dd/mm/yyyy format. Use 'any' if not specified.
        user_availability_start_time: Start time for availability in HH:MM format (24-hour). Use 'any' if not specified.
        user_availability_end_time: End time for availability in HH:MM format (24-hour). Use 'any' if not specified.
        preferred_doctor: Name of preferred doctor. Use 'any' if not specified.
        non_available_days: Dates user is NOT available, separated by ';' in dd/mm/yyyy format. Use 'any' if none specified.

    Returns:
        JSON string containing the query results with available appointment slots.
    """

    # Handle "any" values - provide defaults when user has no specific preferences
    if (
        not user_availability_start_date
        or user_availability_start_date.lower() == "any"
    ):
        # Default to today
        user_availability_start_date = datetime.now().strftime("%d/%m/%Y")

    if not user_availability_end_date or user_availability_end_date.lower() == "any":
        # Default to 2 weeks from start date
        try:
            start_dt: datetime = datetime.strptime(user_availability_start_date, "%d/%m/%Y")
            user_availability_end_date = (start_dt + timedelta(days=14)).strftime(
                "%d/%m/%Y"
            )
        except ValueError:
            user_availability_end_date = (datetime.now() + timedelta(days=14)).strftime(
                "%d/%m/%Y"
            )

    if (
        not user_availability_start_time
        or user_availability_start_time.lower() == "any"
    ):
        user_availability_start_time = "09:00"  # Default to 9 AM

    if not user_availability_end_time or user_availability_end_time.lower() == "any":
        user_availability_end_time = "17:00"  # Default to 5 PM

    # Parse non-available days
    excluded_dates: List[date] = []
    if non_available_days and non_available_days.lower() != "any":
        try:
            # Split by ';' and parse each date
            date_strings: List[str] = non_available_days.split(";")
            for date_str in date_strings:
                date_str = date_str.strip()  # Remove whitespace
                if date_str:  # Skip empty strings
                    excluded_date: date = datetime.strptime(date_str, "%d/%m/%Y").date()
                    excluded_dates.append(excluded_date)
        except ValueError:
            return json.dumps(
                {
                    "success": False,
                    "error": "Some non-available dates couldn't be parsed. Please use dd/mm/yyyy format separated by ';'.",
                    "available_slots": [],
                    "search_criteria": {},
                },
                indent=2,
            )

    try:
        # Parse dates
        start_datetime: datetime = datetime.strptime(user_availability_start_date, "%d/%m/%Y")
        end_datetime: datetime = datetime.strptime(user_availability_end_date, "%d/%m/%Y")

        # Parse times (use default business hours if not provided)
        start_hour: int
        start_minute: int
        if user_availability_start_time:
            start_hour, start_minute = map(int, user_availability_start_time.split(":"))
        else:
            start_hour, start_minute = 9, 0  # Default 9:00 AM

        end_hour: int
        end_minute: int
        if user_availability_end_time:
            end_hour, end_minute = map(int, user_availability_end_time.split(":"))
        else:
            end_hour, end_minute = 17, 0  # Default 5:00 PM

        # Generate available appointment slots
        available_slots: List[str] = generate_appointment_slots(
            start_datetime,
            end_datetime,
            start_hour,
            start_minute,
            end_hour,
            end_minute,
            preferred_doctor,
            excluded_dates,
        )

        # Prepare success response
        result: Dict[str, Any] = {
            "success": True,
            "available_slots": available_slots,
            "total_slots": len(available_slots),
            "search_criteria": {
                "start_date": user_availability_start_date,
                "end_date": user_availability_end_date,
                "start_time": user_availability_start_time,
                "end_time": user_availability_end_time,
                "preferred_doctor": preferred_doctor
                if preferred_doctor and preferred_doctor.lower() != "any"
                else "Any doctor",
                "excluded_dates": [date.strftime("%d/%m/%Y") for date in excluded_dates]
                if excluded_dates
                else [],
            },
        }

        if available_slots:
            if preferred_doctor and preferred_doctor.lower() != "any":
                result["message"] = (
                    f"Found {len(available_slots)} available appointment slots with Dr. {preferred_doctor}"
                )
            else:
                result["message"] = (
                    f"Found {len(available_slots)} available appointment slots"
                )
        else:
            result["message"] = (
                "No appointments are available in your specified time range. Please try a different date or time."
            )

        return result

    except ValueError as e:
        return {
                "success": False,
                "error": "I couldn't understand the date or time format. Please use dd/mm/yyyy for dates and HH:MM for times.",
                "available_slots": [],
                "search_criteria": {},
            }
    except Exception as e:
        return {
                "success": False,
                "error": f"Sorry, there was an error finding appointments: {str(e)}",
                "available_slots": [],
                "search_criteria": {},
            }

@mcp.tool()
def book_appointment(appointment_slot: str) -> Dict[str, Any]:
    """
    Book an appointment at the specified time.
    """
    # mock the booking process
    return {
        "success": True,
        "appointment_confirmed": True,
        "message": f"Appointment booked for {appointment_slot}",
    }

    return result


if __name__ == "__main__":
    print("🚀 Starting FastMCP Appointment Server with HTTP Transport")
    print("📍 Server will start on http://localhost:8002")

    # Use the newer streamable HTTP transport (recommended)
    print("🔗 Using Streamable HTTP transport")
    print("📋 MCP endpoint: http://localhost:8002/mcp")
    print("📋 Connect MCP clients to: http://localhost:8002/mcp")

    # Run with streamable HTTP transport (newer, more reliable)
    mcp.run(transport="http", host="0.0.0.0", port=8002, path="/mcp")
