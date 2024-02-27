import streamlit as st
from optimal_wealth_fraction import merton_share



st.title('Optimal Wealth Fraction Calculator')

# How to use
with st.expander('READ ME'):
    st.markdown("""
            ### Background
            
            > :heavy_exclamation_mark: Currently, the app only supports the S&P500 ETF (ticker: SPY). 
            
            The calculator uses daily stock data to determine the optimal betting fraction of the S&P500 using the Merton Share formula. The key idea is not in maximizing our expected wealth but in maximizing our expected utility. 
            
            **Why?** 
            
            **Expected wealth** is the average financial outcome, focusing on increasing financial assets without considering how they impact happiness or satisfaction. For example, the happiness boost from increasing wealth from \$10,000 to \$100,000 is typically greater than from \$1 million to \$2 million. 
            **Expected utility** focuses on maximizing happiness from financial decisions, considering personal preferences, risk tolerance, and diminishing returns from wealth. Diminishing marginal returns refers to getting less utility the more wealth you acquire. The joy from gaining the first \$1,000 is often greater than from the subsequent \$1,000s.

            ### How it works
            
            Input your amount of wealth available to invest and your risk aversion score.
            
            Risk aversion score:
            - 1 = Risk lover
            - 2 = Balanced
            - 3 = Risk averse
            
            If experiencing any issues, rerun the application. If issues persist, [contact me](saul.chirinos10@gmail.com) with a screenshot of the error.
            
            Feedback is always appreciated :smile:
            
            ---
            
            **Data Sources**
            - S&P500: [Online Data Robert Shiller](http://www.econ.yale.edu/~shiller/data.htm)
            - Risk free rate: [FRED Treasury Inflation-Indexed Note](https://fred.stlouisfed.org/series/DTP10J28)
            
            ---
            
            **Merton Share Formula**
            
            $\hat k = \\frac{\mu - r}{\gamma \sigma^2}$
            
            where,
            - $\hat k$: The optimal betting fraction.
            - $\mu$: The 1/CAPE (Cyclically Adjusted Price-to-Earnings or Shiller P/E or P/E 10), calculated as earnings divided by price over the last 10 years. When the CAPE ratio is high, you are paying a high price for a normalized stream of earnings, and the prospective return of the stock market is low.
            - $r$: The risk free rate, using the latest Treasury Inflation-Protected Securities (TIPS). This is like your alternative risk-free investment option.
            - $\gamma$: The risk aversion score.
            - $\sigma$: The short and long term market volatility. Short term compares the last 3 months and long term compares the last 5 years of data.
            """)


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
        
    except ValueError as e:
        st.error('Please enter a number.')
        st.stop()

    # column_01, column_02, column_03, column_04 = st.columns(4)
    column_01, column_02 = st.columns(2)

    with column_01:
        st.metric('Real Yield (1/CAPE)', f'{round(real_yield*100, 2)}%')
        st.metric('Risk Free Rate (10yr TIPS)', f'{round(risk_free_rate*100, 2)}%')
        st.metric('Optimal Betting Fraction', f'{round(optimal_betting_fraction, 2)}%')

    with column_02:
        st.metric('CAPE', f'{round(real_yield**-1, 2)}')
        st.metric('Market Risk', f'{round(market_risk*100, 2)}%')
        st.metric('Wealth to Invest', f'${wealth*optimal_betting_fraction/100:.02f}')

    # with column_03:

    # with column_04:
        
