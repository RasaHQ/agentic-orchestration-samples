from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from datetime import datetime, timedelta
import random


class ActionQueryAvailableAppointments(Action):
    """
    Custom action to query available appointment slots based on user preferences.

    Handles slot values of "any" by providing sensible defaults:
    - start_date: today
    - end_date: 2 weeks from start_date
    - start_time: 09:00
    - end_time: 17:00
    - preferred_doctor: any available doctor
    - non_available_days: no date restrictions

    Excludes user's non-available days from appointment generation.
    """

    def name(self) -> Text:
        return "query_available_appointments"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Extract slot values
        start_date = tracker.get_slot("user_availability_start_date")
        end_date = tracker.get_slot("user_availability_end_date")
        start_time = tracker.get_slot("user_availability_start_time")
        end_time = tracker.get_slot("user_availability_end_time")
        preferred_doctor = tracker.get_slot("preferred_doctor")
        non_available_days = tracker.get_slot("non_available_days")

        # Handle "any" values - provide defaults when user has no specific preferences
        if not start_date or start_date.lower() == "any":
            # Default to today
            start_date = datetime.now().strftime("%d/%m/%Y")

        if not end_date or end_date.lower() == "any":
            # Default to 2 weeks from start date
            if start_date:
                start_dt = datetime.strptime(start_date, "%d/%m/%Y")
                end_date = (start_dt + timedelta(days=14)).strftime("%d/%m/%Y")
            else:
                end_date = (datetime.now() + timedelta(days=14)).strftime("%d/%m/%Y")

        if not start_time or start_time.lower() == "any":
            start_time = "09:00"  # Default to 9 AM

        if not end_time or end_time.lower() == "any":
            end_time = "17:00"  # Default to 5 PM

        # Parse non-available days
        excluded_dates = []
        if non_available_days and non_available_days.lower() != "any":
            try:
                # Split by ';' and parse each date
                date_strings = non_available_days.split(';')
                for date_str in date_strings:
                    date_str = date_str.strip()  # Remove whitespace
                    if date_str:  # Skip empty strings
                        excluded_date = datetime.strptime(date_str, "%d/%m/%Y").date()
                        excluded_dates.append(excluded_date)
            except ValueError:
                dispatcher.utter_message(text="Some non-available dates couldn't be parsed. Please use dd/mm/yyyy format separated by ';'.")
                return []

        try:
            # Parse dates
            start_datetime = datetime.strptime(start_date, "%d/%m/%Y")
            end_datetime = datetime.strptime(end_date, "%d/%m/%Y")

            # Parse times (use default business hours if not provided)
            if start_time:
                start_hour, start_minute = map(int, start_time.split(':'))
            else:
                start_hour, start_minute = 9, 0  # Default 9:00 AM

            if end_time:
                end_hour, end_minute = map(int, end_time.split(':'))
            else:
                end_hour, end_minute = 17, 0  # Default 5:00 PM

            # Generate available appointment slots
            available_slots = self._generate_appointment_slots(
                start_datetime, end_datetime,
                start_hour, start_minute,
                end_hour, end_minute,
                preferred_doctor,
                excluded_dates
            )

            if available_slots:
                # Format message based on whether doctor preference was specified
                if preferred_doctor and preferred_doctor.lower() != "any":
                    message = f"Here are available appointment slots with Dr. {preferred_doctor}:"
                else:
                    message = "Here are available appointment slots:"

                # Create formatted list for user display
                slot_list = "\n".join([f"• {slot}" for slot in available_slots])
                # dispatcher.utter_message(text=f"{message}\n{slot_list}")

                # Store slots for further processing
                return [SlotSet("available_appointment_slots", available_slots)]
            else:
                dispatcher.utter_message(text="Sorry, no appointments are available in your specified time range. Please try a different date or time.")
                return [SlotSet("available_appointment_slots", [])]

        except ValueError as e:
            dispatcher.utter_message(text="I couldn't understand the date or time format. Please use dd/mm/yyyy for dates and HH:MM for times.")
            return []
        except Exception as e:
            dispatcher.utter_message(text="Sorry, there was an error finding appointments. Please try again.")
            return []

    def _generate_appointment_slots(self, start_date, end_date,
                                  start_hour, start_minute,
                                  end_hour, end_minute,
                                  preferred_doctor, excluded_dates):
        """Generate up to 3 realistic appointment slots within the given constraints,
        excluding user's non-available days"""

        slots = []
        current_date = start_date
        max_slots = 10

        # Define typical appointment duration (30 minutes)
        appointment_duration = timedelta(minutes=30)

        # Ensure we don't generate appointments outside business hours (8 AM - 6 PM)
        business_start = max(start_hour, 8)
        business_end = min(end_hour, 18)

        # If the time range doesn't overlap with business hours, adjust
        if business_start >= business_end:
            business_start = 9
            business_end = 17

        attempts = 0
        max_attempts = 50  # Prevent infinite loops

        while len(slots) < max_slots and current_date <= end_date and attempts < max_attempts:
            attempts += 1

            # Check if current date is in user's non-available days
            if current_date.date() in excluded_dates:
                current_date += timedelta(days=1)
                continue

            # Skip weekends for realistic doctor appointments
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4

                # Generate random hour and minute within business hours
                random_hour = random.randint(business_start, business_end - 1)

                # Round minutes to common appointment times (00, 15, 30, 45)
                random_minute = random.choice([0, 15, 30, 45])

                # Ensure the appointment fits within user's time preferences
                appointment_time = current_date.replace(
                    hour=random_hour,
                    minute=random_minute,
                    second=0,
                    microsecond=0
                )

                # Check if appointment time is within user's daily availability
                user_start_time = current_date.replace(hour=start_hour, minute=start_minute)
                user_end_time = current_date.replace(hour=end_hour, minute=end_minute)

                if user_start_time <= appointment_time <= (user_end_time - appointment_duration):
                    # Format: dd/mm/yyyy ; HH:MM
                    formatted_slot = appointment_time.strftime("%d/%m/%Y ; %H:%M")

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
                additional_date = start_date + timedelta(days=i + 1)

                # Skip if date is excluded or weekend
                if (additional_date.date() in excluded_dates or
                    additional_date.weekday() >= 5 or
                    additional_date > end_date):
                    continue

                additional_hour = random.randint(business_start, business_end - 1)
                additional_minute = random.choice([0, 15, 30, 45])

                additional_time = additional_date.replace(
                    hour=additional_hour,
                    minute=additional_minute
                )

                formatted_slot = additional_time.strftime("%d/%m/%Y ; %H:%M")
                if formatted_slot not in slots:
                    slots.append(formatted_slot)

        print(slots)
        return slots[:max_slots]  # Ensure we return at most 3 slots
