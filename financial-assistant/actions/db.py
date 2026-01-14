import os
import shutil
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from rasa.nlu.utils import write_json_to_file
from rasa.shared.utils.io import read_json_file

ORIGIN_DB_PATH = "db"
CREDIT_CARDS = "credit_cards.json"
TRANSACTIONS = "transactions.json"
USER_PROFILE = "user_profile.json"


# =============================================================================
# Data Models
# =============================================================================


class CreditCard(BaseModel):
    id: str
    last_four: str
    type: str
    balance_due: float
    credit_limit: float
    due_date: str
    is_locked: bool = False
    is_lost: bool = False


class Transaction(BaseModel):
    id: str
    card_id: str
    merchant: str
    category: str
    amount: float
    currency: str
    timestamp: str
    location: str
    is_disputed: bool = False


class LoyaltyMembership(BaseModel):
    program: str
    tier: str
    member_since: str


class UserPreferences(BaseModel):
    travel_heavy: bool = False
    preferred_airlines: List[str] = []
    notification_method: str = "email"


class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    loyalty_memberships: List[LoyaltyMembership] = []
    preferences: UserPreferences = UserPreferences()
    linked_cards: List[str] = []


# =============================================================================
# Database Helpers
# =============================================================================


def get_session_db_path(session_id: str) -> str:
    tempdir = tempfile.gettempdir()
    project_name = "financial_assistant"
    return os.path.join(tempdir, project_name, session_id)


def prepare_db_file(session_id: str, db: str) -> str:
    session_db_path = get_session_db_path(session_id)
    os.makedirs(session_db_path, exist_ok=True)
    destination_file = os.path.join(session_db_path, db)
    if not os.path.exists(destination_file):
        origin_file = os.path.join(ORIGIN_DB_PATH, db)
        shutil.copy(origin_file, destination_file)
    return destination_file


def read_db(session_id: str, db: str) -> Any:
    db_file = prepare_db_file(session_id, db)
    return read_json_file(db_file)


def write_db(session_id: str, db: str, data: Any) -> None:
    db_file = prepare_db_file(session_id, db)
    write_json_to_file(db_file, data)


# =============================================================================
# Credit Card Operations
# =============================================================================


def get_credit_cards(session_id: str) -> List[CreditCard]:
    """Get all credit cards for the user."""
    return [CreditCard(**item) for item in read_db(session_id, CREDIT_CARDS)]


def get_card_by_last_four(session_id: str, last_four: str) -> Optional[CreditCard]:
    """Find a credit card by its last 4 digits."""
    cards = get_credit_cards(session_id)
    for card in cards:
        if card.last_four == last_four:
            return card
    return None


def get_card_by_id(session_id: str, card_id: str) -> Optional[CreditCard]:
    """Find a credit card by its ID."""
    cards = get_credit_cards(session_id)
    for card in cards:
        if card.id == card_id:
            return card
    return None


def update_card(session_id: str, updated_card: CreditCard) -> bool:
    """Update a credit card in the database."""
    cards = get_credit_cards(session_id)
    for i, card in enumerate(cards):
        if card.id == updated_card.id:
            cards[i] = updated_card
            write_db(session_id, CREDIT_CARDS, [c.model_dump() for c in cards])
            return True
    return False


def lock_card(session_id: str, card_id: str) -> bool:
    """Lock a credit card."""
    card = get_card_by_id(session_id, card_id)
    if card:
        card.is_locked = True
        return update_card(session_id, card)
    return False


def report_card_lost(session_id: str, card_id: str) -> bool:
    """Mark a card as lost."""
    card = get_card_by_id(session_id, card_id)
    if card:
        card.is_lost = True
        return update_card(session_id, card)
    return False


def pay_card_bill(
    session_id: str, card_id: str, amount: float
) -> Dict[str, Any]:
    """Pay towards a credit card bill."""
    card = get_card_by_id(session_id, card_id)
    if not card:
        return {"success": False, "error": "Card not found"}

    if amount <= 0:
        return {"success": False, "error": "Invalid payment amount"}

    if amount > card.balance_due:
        return {"success": False, "error": "Payment exceeds balance due"}

    card.balance_due = round(card.balance_due - amount, 2)
    update_card(session_id, card)

    return {
        "success": True,
        "amount_paid": amount,
        "new_balance": card.balance_due,
        "card_last_four": card.last_four,
    }


# =============================================================================
# Transaction Operations
# =============================================================================


def get_transactions(session_id: str) -> List[Transaction]:
    """Get all transactions."""
    return [Transaction(**item) for item in read_db(session_id, TRANSACTIONS)]


def get_transactions_by_card(
    session_id: str, card_id: str, limit: Optional[int] = None
) -> List[Transaction]:
    """Get transactions for a specific card, sorted by most recent first."""
    transactions = get_transactions(session_id)
    card_transactions = [t for t in transactions if t.card_id == card_id]
    # Sort by timestamp descending
    card_transactions.sort(key=lambda t: t.timestamp, reverse=True)
    if limit:
        return card_transactions[:limit]
    return card_transactions


def get_transaction_by_id(session_id: str, txn_id: str) -> Optional[Transaction]:
    """Find a transaction by ID."""
    transactions = get_transactions(session_id)
    for txn in transactions:
        if txn.id == txn_id:
            return txn
    return None


def dispute_transaction(session_id: str, txn_id: str) -> bool:
    """Mark a transaction as disputed."""
    transactions = get_transactions(session_id)
    for i, txn in enumerate(transactions):
        if txn.id == txn_id:
            transactions[i].is_disputed = True
            write_db(session_id, TRANSACTIONS, [t.model_dump() for t in transactions])
            return True
    return False


def dispute_transactions(session_id: str, txn_ids: List[str]) -> Dict[str, Any]:
    """Dispute multiple transactions."""
    transactions = get_transactions(session_id)
    disputed_count = 0

    for i, txn in enumerate(transactions):
        if txn.id in txn_ids:
            transactions[i].is_disputed = True
            disputed_count += 1

    if disputed_count > 0:
        write_db(session_id, TRANSACTIONS, [t.model_dump() for t in transactions])

    return {
        "success": disputed_count > 0,
        "disputed_count": disputed_count,
        "requested_count": len(txn_ids),
    }


def get_transactions_by_merchant(
    session_id: str, merchant: str, card_id: Optional[str] = None
) -> List[Transaction]:
    """Find transactions by merchant name (case-insensitive partial match)."""
    transactions = get_transactions(session_id)
    results = []
    merchant_lower = merchant.lower()

    for txn in transactions:
        if merchant_lower in txn.merchant.lower():
            if card_id is None or txn.card_id == card_id:
                results.append(txn)

    return results


def get_transactions_by_date(
    session_id: str, date_str: str, card_id: Optional[str] = None
) -> List[Transaction]:
    """Find transactions by date (YYYY-MM-DD format)."""
    transactions = get_transactions(session_id)
    results = []

    for txn in transactions:
        txn_date = txn.timestamp[:10]  # Extract YYYY-MM-DD
        if txn_date == date_str:
            if card_id is None or txn.card_id == card_id:
                results.append(txn)

    return results


# =============================================================================
# User Profile Operations
# =============================================================================


def get_user_profile(session_id: str) -> UserProfile:
    """Get the user's profile."""
    data = read_db(session_id, USER_PROFILE)

    # Handle nested models
    memberships = [
        LoyaltyMembership(**m) for m in data.get("loyalty_memberships", [])
    ]
    preferences = UserPreferences(**data.get("preferences", {}))

    return UserProfile(
        user_id=data["user_id"],
        name=data["name"],
        email=data["email"],
        loyalty_memberships=memberships,
        preferences=preferences,
        linked_cards=data.get("linked_cards", []),
    )


def get_loyalty_memberships(session_id: str) -> List[LoyaltyMembership]:
    """Get user's loyalty program memberships."""
    profile = get_user_profile(session_id)
    return profile.loyalty_memberships


def has_loyalty_membership(session_id: str, program: str) -> Optional[LoyaltyMembership]:
    """Check if user has a specific loyalty membership."""
    memberships = get_loyalty_memberships(session_id)
    program_lower = program.lower()

    for membership in memberships:
        if program_lower in membership.program.lower():
            return membership

    return None
