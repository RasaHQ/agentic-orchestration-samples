import json


class MockFinancingAPI:
    """
    A mock API server for financing options, simulating a bank's internal service.
    It calculates estimated loan payments and impact of using savings.
    """

    def __init__(self):
        # Hard-coded typical annual interest rates for demo purposes (as percentages)
        # In a real scenario, these would come from dynamic data or a rate engine.
        self.annual_interest_rates = {
            36: 4.5,  # 36 months ~ 3 years
            48: 5.0,  # 48 months ~ 4 years
            60: 5.5,  # 60 months ~ 5 years
            72: 6.0,  # 72 months ~ 6 years
        }

    def _calculate_monthly_payment(
        self, principal: float, annual_rate: float, loan_term_months: int
    ):
        """
        Calculates the estimated monthly loan payment and total interest paid.
        Formula: P * [i(1 + i)^n] / [(1 + i)^n – 1]
        Where P = Principal, i = monthly interest rate, n = number of months
        """
        if loan_term_months <= 0:
            return 0.0, 0.0  # Avoid division by zero

        monthly_rate = (annual_rate / 100) / 12

        if (
            monthly_rate == 0
        ):  # Simple interest if rate is zero (unlikely for real loans)
            monthly_payment = principal / loan_term_months
            total_interest = 0.0
        else:
            numerator = monthly_rate * (1 + monthly_rate) ** loan_term_months
            denominator = (1 + monthly_rate) ** loan_term_months - 1
            # Handle cases where denominator might be zero if term is 0 or rate is 0
            if denominator == 0:
                return 0.0, 0.0

            monthly_payment = principal * (numerator / denominator)
            total_interest = (monthly_payment * loan_term_months) - principal

        return round(monthly_payment, 2), round(total_interest, 2)

    def calculate_loan_details(
        self,
        purchase_amount: float,
        loan_term_months: int,
        available_savings_balance: float,
        down_payment: float = None,
    ):
        """
        Calculates loan details, including monthly payment, total interest, and savings impact.
        Can optionally take a down payment.

        Args:
            purchase_amount (float): The total price of the car.
            loan_term_months (int): Desired loan term in months (e.g., 36, 48, 60).
            available_savings_balance (float): The user's current savings balance known by the bank.
            down_payment (float, optional): The amount of down payment. Defaults to None.

        Returns:
            str: A JSON string with financing estimates and savings impact, or an error.
        """
        print(
            f"DEBUG (MockFinancingAPI): calculate_loan_details called with: "
            f"purchase_amount={purchase_amount}, loan_term_months={loan_term_months}, "
            f"available_savings_balance={available_savings_balance}, down_payment={down_payment}"
        )

        response_data = {
            "error": None,
            "monthly_payment_estimate": 0.0,
            "total_interest_paid": 0.0,
            "principal_financed": purchase_amount,
            "remaining_savings_after_dp": available_savings_balance,
            "savings_impact_if_cash": "",
        }

        # Validate loan term
        annual_rate = self.annual_interest_rates.get(loan_term_months)
        if annual_rate is None:
            response_data["error"] = (
                f"Invalid loan term. Supported terms: {list(self.annual_interest_rates.keys())} months."
            )
            return json.dumps(response_data)

        # Handle down payment
        principal_to_finance = purchase_amount
        if down_payment is not None:
            if down_payment < 0:
                response_data["error"] = "Down payment cannot be negative."
                return json.dumps(response_data)
            if down_payment > purchase_amount:
                response_data["error"] = "Down payment cannot exceed purchase amount."
                return json.dumps(response_data)

            principal_to_finance = purchase_amount - down_payment
            response_data["principal_financed"] = round(principal_to_finance, 2)
            response_data["remaining_savings_after_dp"] = round(
                available_savings_balance - down_payment, 2
            )
        else:
            # If no down payment, remaining savings is simply the available balance
            response_data["remaining_savings_after_dp"] = round(
                available_savings_balance, 2
            )

        # Calculate monthly payment and total interest
        monthly_payment, total_interest = self._calculate_monthly_payment(
            principal_to_finance, annual_rate, loan_term_months
        )
        response_data["monthly_payment_estimate"] = monthly_payment
        response_data["total_interest_paid"] = total_interest

        # Calculate savings impact if user were to pay cash (always included)
        if available_savings_balance >= purchase_amount:
            response_data["savings_impact_if_cash"] = (
                f"You could pay cash, leaving €{available_savings_balance - purchase_amount:.2f} in savings."
            )
        else:
            response_data["savings_impact_if_cash"] = (
                f"Paying cash would require an additional €{purchase_amount - available_savings_balance:.2f}."
            )

        return json.dumps(response_data)


# Example usage (for testing this module standalone)
if __name__ == "__main__":
    financing_api = MockFinancingAPI()

    # Test 1: Initial financing options (no down payment)
    result1 = financing_api.calculate_loan_details(
        purchase_amount=28000.0, loan_term_months=60, available_savings_balance=15500.0
    )
    print("\n--- Test 1: Initial Financing (No Down Payment) ---")
    print(json.dumps(json.loads(result1), indent=2))

    # Test 2: Financing with a specific down payment
    result2 = financing_api.calculate_loan_details(
        purchase_amount=28000.0,
        loan_term_months=60,
        available_savings_balance=15500.0,
        down_payment=1000.0,
    )
    print("\n--- Test 2: Financing (with €1000 Down Payment) ---")
    print(json.dumps(json.loads(result2), indent=2))

    # Test 3: Financing with a different down payment
    result3 = financing_api.calculate_loan_details(
        purchase_amount=28000.0,
        loan_term_months=60,
        available_savings_balance=15500.0,
        down_payment=7000.0,
    )
    print("\n--- Test 3: Financing (with €7000 Down Payment) ---")
    print(json.dumps(json.loads(result3), indent=2))

    # Test 4: Down payment exceeds purchase amount
    result4 = financing_api.calculate_loan_details(
        purchase_amount=28000.0,
        loan_term_months=60,
        available_savings_balance=15500.0,
        down_payment=30000.0,
    )
    print("\n--- Test 4: Down Payment Exceeds Purchase ---")
    print(json.dumps(json.loads(result4), indent=2))

    # Test 5: Invalid loan term
    result5 = financing_api.calculate_loan_details(
        purchase_amount=28000.0, loan_term_months=99, available_savings_balance=15500.0
    )
    print("\n--- Test 5: Invalid Loan Term ---")
    print(json.dumps(json.loads(result5), indent=2))
