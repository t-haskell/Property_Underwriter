import streamlit as st
from core.models import Address, RentalAssumptions, FlipAssumptions

def address_input() -> Address | None:
    st.subheader("Property Address")
    col1, col2 = st.columns(2)
    line1 = st.text_input("Street Address")
    city = col1.text_input("City")
    state = col2.text_input("State (e.g., MA)")
    zipc = st.text_input("ZIP")
    if line1 and city and state and zipc:
        return Address(line1=line1, city=city, state=state, zip=zipc)
    return None

def analysis_choice() -> str:
    return st.sidebar.radio("Analysis Type", ["Rental Analysis", "Renovation Flip Analysis"])

def rental_form() -> tuple[RentalAssumptions, float]:
    st.subheader("Rental Assumptions")
    # Minimal; add all fields with sensible defaults
    price = st.number_input("Purchase Price", min_value=0.0, value=350000.0, step=1000.0)
    down = st.number_input("Down Payment %", 0.0, 100.0, 20.0)
    rate = st.number_input("Interest Rate (annual %)", 0.0, 20.0, 6.5)
    term = st.number_input("Loan Term (years)", 1, 40, 30)
    vac = st.number_input("Vacancy %", 0.0, 50.0, 5.0)
    mgmt = st.number_input("Property Mgmt %", 0.0, 30.0, 8.0)
    hold = st.number_input("Hold Period (years)", 1, 40, 5)
    insurance = st.number_input("Insurance (annual $)", 0.0, 100000.0, 1200.0)
    hoa = st.number_input("HOA (annual $)", 0.0, 100000.0, 0.0)
    # maint = st.number_input("Maintenance Reserve (annual $)", 0.0, 100000.0, 1200.0)
    capex = st.number_input("CapEx Reserve (annual $)", 0.0, 100000.0, 1200.0)
    target_cap = st.number_input("Target Cap Rate % (optional)", 0.0, 50.0, 0.0)
    # a = RentalAssumptions(down, rate/100, term, vac, maint, capex, insurance, hoa, mgmt, hold,
    #                       target_cap_rate_pct=(target_cap if target_cap > 0 else None))
    a = RentalAssumptions(down, rate/100, term, vac, capex, insurance, hoa, mgmt, hold,
                          target_cap_rate_pct=(target_cap if target_cap > 0 else None))
    return a, price

def flip_form() -> tuple[FlipAssumptions, float]:
    st.subheader("Flip Assumptions")
    price = st.number_input("Candidate Purchase Price", min_value=0.0, value=250000.0, step=1000.0)
    down = st.number_input("Down Payment %", 0.0, 100.0, 20.0)
    rate = st.number_input("Interest Rate (annual %)", 0.0, 20.0, 6.5)
    term = st.number_input("Loan Term (months)", 1, 1000, 30)
    reno = st.number_input("Renovation Budget", 0.0, 5_000_000.0, 60000.0)
    hold_m = st.number_input("Hold Time (months)", 1, 60, 6)
    margin = st.number_input("Target Margin (% of ARV)", 0.0, 50.0, 10.0)
    buy = st.number_input("Closing Costs on Buy (% of price)", 0.0, 10.0, 2.0)
    sell = st.number_input("Closing Costs on Sell (% of ARV)", 0.0, 10.0, 6.0)
    #carry = st.number_input("Carry Costs (monthly)", 0.0, 100000.0, 1200.0)
    arv_override = st.number_input("ARV Override (optional)", 0.0, 100000000.0, 0.0)
    # a = FlipAssumptions(renovation_budget=reno, hold_time_months=hold_m,
    #                     target_margin_pct=margin/100, closing_pct_buy=buy/100,
    #                     closing_pct_sell=sell/100, carry_costs_monthly=carry,
    #                     arv_override=(arv_override if arv_override > 0 else None))
    a = FlipAssumptions(down_payment_pct=down, interest_rate_annual=rate/100, loan_term_years=term, renovation_budget=reno, hold_time_months=hold_m,
                        target_margin_pct=margin/100, closing_pct_buy=buy/100,
                        closing_pct_sell=sell/100, arv_override=(arv_override if arv_override > 0 else None))
    return a, price 