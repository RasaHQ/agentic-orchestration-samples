# Financial Agent

A [financial agent](https://github.com/RasaHQ/agentic-orchestration-samples/tree/memory-poc/financial-assistant) built with Rasa that helps users manage credit cards, view transactions, pay bills, set reminders, and handle disputes.

The agent supports the following flows:

| Capability | Description |
| --- | --- |
| **List credit cards** | List all credit cards on the account with balance and due date. |
| **List / filter transactions** | Show transactions for a card, with optional filters by merchant, date, category, amount, or location (e.g. "transactions at Starbucks", "last week"). |
| **Pay credit card bill** | Pay towards a card balance: specify card (last 4 digits), amount, and confirm. |
| **Set payment reminder** | Set when and how to be reminded to pay (e.g. 3 days before due date, via email, SMS, or push). |
| **Lock credit card** | Lock a card to prevent new transactions; requires confirmation. |
| **Report lost card** | Report a card as lost or stolen and optionally lock it; replacement can be mailed. |
| **Credit card offers (agentic)** | Get personalized card recommendations based on spending habits, rewards preference, annual fee tolerance, and travel frequency. |
| **Dispute transaction (agentic)** | Dispute one or more transactions for fraud investigation; can reference transactions from a list (e.g. by date, merchant, or "the second one"). |

## Highlights

This demo illustrates two concepts:

1. **Composable agents** — The assistant uses modular, composable skills that handle specialized tasks (e.g. disputes, credit card recommendations) and can be invoked or switched between during a conversation. See [Composable Agents](https://www.notion.so/Composable-Agents-2aab9c0d544a80238549c0c63c347df9?pvs=21) for more.
2. **Memory** — The assistant uses persistent memory to track user information, preferences, and conversation context, enabling follow-up questions on just-shown information and more personalized replies. See [Memory, Context, & Personalized Conversations](https://www.notion.so/Memory-Context-Personalized-Conversations-2dfb9c0d544a8095b513ebfbacc8a984?pvs=21) for more.

## Structure

```
financial-assistant/
├── project/                    # Project-wide config and shared assets
│   ├── config.yml              # Rasa config (pipeline, policies, command generator)
│   ├── integrations.yml        # Endpoints (tracker, actions, etc.)
│   ├── memory.yml              # Shared slots (e.g. return_value)
│   ├── responses.yml           # (if present) project-level responses
│   ├── default_skills/
│   │   └── default_flows.yml   # Default flows & patterns (e.g. continue conversation, cancel)
│   ├── prompts/
│   │   └── command_generator_prompt_template.jinja2   # LLM prompt for command generation
│   └── custom_components/      # Python implementations for agent flows
│       ├── credit_card_offers_agent.py
│       └── transaction_agent.py
├── skills/                     # Domain skills (cards, payments, transactions)
│   ├── cards/
│   │   ├── memory.yml          # Slots used by card flows
│   │   ├── flows/              # list_cards, lock_card, report_lost_card, credit_card_offers_agent
│   │   └── prompts/            # Agent prompt for credit card offers
│   ├── payments/
│   │   ├── memory.yml
│   │   └── flows/              # pay_credit_card_bill, set_payment_reminder
│   └── transaction_handling/
│       ├── memory.yml
│       ├── flows/              # list_transactions, transaction_agent
│       └── prompts/            # Agent prompt for transaction disputes
└── db/                         # Mock data for the demo
    ├── credit_cards.json
    ├── transactions.json
    └── user_profile.json
```

- **project/** — Global configuration, shared slots, default patterns, and the command-generator prompt. Custom components here implement the logic for agent flows (credit card offers, transaction disputes).
- **skills/** — Each skill (cards, payments, transaction_handling) groups its flows, skill-specific slots (`memory.yml`), and any agent prompts.
- **db/** — JSON data used by actions (cards, transactions, user profile) for the POC.

## Set Up

1. **Get the financial agent** — Clone [agentic-orchestration-samples](https://github.com/RasaHQ/agentic-orchestration-samples) and check out the `memory-poc` branch. The financial agent is in the `financial-assistant/` directory.
2. **Install Rasa** — Install Rasa from the `memory-poc` branch (e.g. clone the [Rasa repo](https://github.com/RasaHQ/rasa-private), checkout the `memory-poc` branch, and then run `make install` in the Rasa repo root).
3. **Train** — From the `financial-assistant/` directory, run `rasa train --skip-validation` (validation logic has not been updated for this POC).
4. **Interact** — Run the assistant and use the inspector: `rasa inspect --nextgen`.
