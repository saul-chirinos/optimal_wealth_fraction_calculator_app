import streamlit as st
import plotly.graph_objs as go

import optimal_wealth_fraction as owf

st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)


# Initialize session state variables if they don't exist
if 'initialized' not in st.session_state:
    st.session_state['initialized'] = True
    st.session_state['wealth'] = 1000  # Default
    st.session_state['risk_aversion'] = 2  # Default
    st.session_state['long_term_weight'] = 0.5  # Default


st.title('Optimal Wealth Fraction Calculator')

with st.expander('READ ME'):
    st.markdown("""
            ##### Background
            
            > :heavy_exclamation_mark: Currently, the app only supports the S&P500 ETF (ticker: SPY). 
            
            The calculator uses daily stock data to determine the optimal betting fraction of the S&P500 using the Merton Share formula. The key idea is not in maximizing our expected wealth but in maximizing our expected utility. 
            
            **Why?** 
            
            **Expected wealth** is the average financial outcome, focusing on increasing financial assets without considering how they impact happiness or satisfaction. For example, the happiness boost from increasing wealth from \$10,000 to \$100,000 is typically greater than from \$1 million to \$2 million. 
            **Expected utility** focuses on maximizing happiness from financial decisions, considering personal preferences, risk tolerance, and diminishing returns from wealth. Diminishing marginal returns refers to getting less utility the more wealth you acquire. The joy from gaining the first \$1,000 is often greater than from the subsequent \$1,000s.

            ##### How it works
            
            1. Input your amount of wealth available to invest.
            2. Input your risk aversion score.
            
                Risk aversion score:
                - 1 = Risk taker
                - 2 = Balanced
                - 3 = Risk averse
            
            2. Select how much weight to apply for long term market risk (past 5 years of data variability). The weight for long term market risk and the weight for short term market risk sum up to 1. Meaning that if the long-term risk weight is set to 0.6, then the short-term risk weight is automatically set to 0.4.
            
            If experiencing any issues, rerun the application. If issues persist, [contact me](saul.chirinos10@gmail.com) with a screenshot of the error.
            
            Feedback is always appreciated :smile:
            
            ---
            
            ##### Data
                       
            - S&P500 Prices: [Rapid API](https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-finance-data)
            - S&P500 PE Ratio: [Longtermtrends](https://www.longtermtrends.net/sp500-price-earnings-shiller-pe-ratio/)
            - Risk Free Rate: [FRED Treasury Inflation-Indexed Note](https://fred.stlouisfed.org/series/DTP10J28)
            
            ---
            
            ##### Merton Share Formula
            
            $\hat k = \\frac{\mu - r}{\gamma \sigma^2}$
            
            where,
            - $\hat k$: The optimal betting fraction.
            - $\mu$: The 1/CAPE (Cyclically Adjusted Price-to-Earnings or Shiller P/E or P/E 10), calculated as earnings divided by price over the last 10 years. When the CAPE ratio is high, you are paying a high price for a normalized stream of earnings, and the prospective return of the stock market is low.
            - $r$: The risk free rate, using the latest Treasury Inflation-Protected Securities (TIPS). This is like your alternative risk-free investment option.
            - $\gamma$: The risk aversion score.
            - $\sigma$: The short and long term market volatility. Short term compares the last 3 months and long term compares the last 5 years of data.
            """)



container = st.container()

column01, _ = container.columns(2)
with column01:
    column11, column21, column31 = st.columns(3)
    
    with column11:
        wealth = st.number_input('Investable Wealth', min_value=0, step=100)
    
    with column21:
        risk_aversion = st.number_input('Risk Aversion', 1, 3, value=2, step=1)
        st.session_state['risk_aversion'] = risk_aversion
    
    with column31:
        long_term_weight = st.slider('Long Term Volatility Weight', min_value=0.25, max_value=1.0, value=st.session_state['long_term_weight'], step=0.05)
        st.session_state['longterm_weight'] = long_term_weight
 


st.session_state['df'] = owf.collect_data('SPY')
session_df = st.session_state.get('df')

session_df = owf.prelim_calculations(session_df)
session_df = owf.merton_share(session_df, risk_aversion)

st.session_state['df'] = owf.update_risk(session_df, risk_aversion, long_term_weight)
session_df = st.session_state.get('df')

latest_real_yield = session_df['Real_Yield'].iloc[-1]
latest_risk_free_rate = session_df['TIPS_10yr'].iloc[-1]
latest_cape = session_df['CAPE'].iloc[-1]
latest_market_risk = session_df['Market_Risk'].iloc[-1]
latest_obf = session_df['Optimal_Bet_Fraction'].iloc[-1] / 100

st.session_state['wealth'] = wealth

    
# Display key metrics        
with container:
    st.header('S&P 500')
    
    column21, column22, column32, column42, column52, column62 = st.columns(6)
    with column21:
        st.metric('Real Yield (1/CAPE)', f'{latest_real_yield*100:.1f}%')
    
    with column22:
        st.metric('Market Risk', f'{latest_market_risk*100:.1f}%')

    with column32:
        st.metric('Risk Free Rate', f'{latest_risk_free_rate*100:.1f}%')

    with column42:
        st.metric('CAPE', f'{latest_cape:.2f}')

    with column52:
        st.metric('Optimal Betting Fraction', f'{latest_obf*100:.1f}%')

    with column62:
        st.metric('Wealth to Invest', f'${wealth*latest_obf:,.00f}')
        

# Plots
column03, column04 = st.columns(2)
with column03:
    with st.expander('**Historical Optimal Bet Fraction**'):
        # Plot for optimal bet fraction
        _ = session_df[session_df['Optimal_Bet_Fraction'].notnull()]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=_.index, y=_['Optimal_Bet_Fraction'], name="Optimal Bet Fraction"))
        fig.update_layout(title_text="", xaxis_title="Date", yaxis_title="Percent (%)")
        fig.update_yaxes(tickprefix="", ticksuffix="%", showgrid=True)
        st.plotly_chart(fig)

    with st.expander('**Historical Price**'):
        # Plot for close price
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=session_df.index, y=session_df['Close'], name="Close Price"))
        fig.update_layout(title_text="", xaxis_title="Date", yaxis_title="Price")
        fig.update_yaxes(tickprefix="$", ticksuffix="", showgrid=True)
        st.plotly_chart(fig)

    with st.expander('**Historical CAPE (Shiller PE 10 Ratio)**'):
        # Plot for CAPE
        _ = session_df[session_df['CAPE'].notnull()]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=_.index, y=_['CAPE'], name="CAPE"))
        fig.update_layout(title_text="", xaxis_title="Date", yaxis_title="S&P500 PE 10")
        st.plotly_chart(fig)


with column04:
    with st.expander('**Historical Market Risk**'):
        # Plot for market volatility                   
        _ = session_df[session_df['Market_Risk'].notnull()]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=_.index, y=_['Market_Risk']*100, name="Market Risk"))
        fig.update_layout(title_text="", xaxis_title="Date", yaxis_title="Percent (%)")
        fig.update_yaxes(tickprefix="", ticksuffix="%", showgrid=True)
        st.plotly_chart(fig)

    with st.expander('**Historical Real Yield and 10-Yr Treasury**'):
        # Plot for TIPS_10yr and Real_Yield
        _ = session_df[session_df['TIPS_10yr'].notnull()]
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=_.index, y=_['TIPS_10yr']*100, name="TIPS 10yr", marker_color='Green'))
        fig.add_trace(go.Scatter(x=_.index, y=_['Real_Yield']*100, name="S&P500 Real Yield", marker_color='RoyalBlue'))
        fig.update_layout(
            title_text="",
            xaxis_title="Date",
            yaxis_title="Percent %",
            yaxis_range=[
                min(_['TIPS_10yr'].min()*100, _['Real_Yield'].min()*100), 
                max(_['TIPS_10yr'].max()*100, _['Real_Yield'].max()*100)
            ]
        )
        fig.update_yaxes(tickprefix="", ticksuffix="%", showgrid=True)
        st.plotly_chart(fig)

        
            