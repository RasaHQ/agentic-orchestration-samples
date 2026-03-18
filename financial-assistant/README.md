# Financial Assistant

A conversational financial assistant built with Rasa that helps users manage credit cards, view transactions, pay bills, set reminders, and handle disputes.

## Capabilities

The assistant supports the following flows and agents:

| Capability | Description |
| ---------- | ----------- |
| **List credit cards** | List all credit cards on the account with balance and due date. |
| **List / filter transactions** | Show transactions for a card, with optional filters by merchant, date, category, amount, or location (e.g. "transactions at Starbucks", "last week"). |
| **Pay credit card bill** | Pay towards a card balance: specify card (last 4 digits), amount, and confirm. |
| **Set payment reminder** | Set when and how to be reminded to pay (e.g. 3 days before due date, via email, SMS, or push). |
| **Lock credit card** | Lock a card to prevent new transactions; requires confirmation. |
| **Report lost card** | Report a card as lost or stolen and optionally lock it; replacement can be mailed. |
| **Credit card offers (agent)** | Get personalized card recommendations based on spending habits, rewards preference, annual fee tolerance, and travel frequency. |
| **Dispute transaction (agent)** | Dispute one or more transactions for fraud investigation; can reference transactions from a list (e.g. by date, merchant, or "the second one"). |

The assistant can switch between flows in one conversation (e.g. view transactions, then dispute one, then lock the card) and can answer follow-up questions about information it just showed (e.g. "What did I spend on?" after showing a balance).

## How to run

**Prerequisites:** Python environment with project dependencies installed. **Rasa must be installed from the `memory-poc` branch**.

1. **Train the model** (from the project root, e.g. `financial-assistant/`):

   ```bash
   rasa train --skip-validation
   ```

2. **Run the assistant**:

   ```bash
   rasa inspect --nextgen
   ```
