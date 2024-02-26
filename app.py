import streamlit as st
from optimal_wealth_fraction import merton_share



# Set the title of the web app
st.title('Optimal Wealth Fraction Calculator')

# Section 1: Text Input
st.header('S&P500')

column1, column2 = st.columns(2)
with column1:
    wealth = st.text_input('Investable Wealth')
    
with column2:
    risk_aversion = st.slider('Risk Aversion', 1, 3)

submit_button = st.button('Submit')

real_yield, risk_free_rate, market_risk, optimal_betting_fraction = merton_share(risk_aversion)

if submit_button:
    try:
        wealth = float(wealth)
    except TypeError as e:
        st.error('Please enter a valid number.')
        st.stop()

    column_01, column_02, column_03, column_04 = st.columns(4)

    with column_01:
        st.metric('Real Yield', f'{round(real_yield*100, 2)}%')

    with column_02:
        st.metric('Risk Free Rate', f'{round(risk_free_rate*100, 2)}%')

    with column_03:
        st.metric('Market Risk', f'{round(market_risk*100, 2)}%')

    with column_04:
        st.metric('Optimal Betting Fraction', f'{round(optimal_betting_fraction, 2)}%')
        
    st.metric('Wealth to invest', f'${wealth*optimal_betting_fraction/100:.02f}')
