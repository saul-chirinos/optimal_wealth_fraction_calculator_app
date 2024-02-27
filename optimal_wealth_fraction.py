import os
import pandas as pd
import requests
import streamlit as st
import xlrd


FRED_API_KEY = os.getenv('FRED_API_KEY')
# from config import FRED_API_KEY  # Remove when pushing to github


def get_shiller_pe_ratio():
    """Returns the current CAPE of the SP500.

    Returns:
        _type_: _description_
    """
    url = 'http://www.econ.yale.edu/~shiller/data/ie_data.xls'

    response = requests.get(url)
    
    if response.status_code == 200:
        with open('Data/shiller_data.xls', 'wb') as file:
            file.write(response.content)
            data = pd.read_excel('Data/shiller_data.xls', sheet_name='Data', skiprows=7, usecols='A, M')  # Date, CAPE
            
            data = data.dropna().reset_index(drop=True)
            cape = data.iloc[-1, 1]  # Cyclically Adjusted PE Ratio aka Shiller PE Ratio
            
            return cape
    else:
        print("Failed to retrieve Shiller data document.")
        return None
    

def get_risk_free_rate():
    # play around with param frequency (d default): d = Daily, w = Weekly, bw = Biweekly, m = Monthly, q = Quarterly, sa = Semiannual, a = Annual
    url = f'https://api.stlouisfed.org/fred/series/observations?series_id=DTP10J28&api_key={FRED_API_KEY}&frequency=d&sort_order=desc&file_type=json'
    response = requests.get(url)
    
    try:
        assert response.status_code == 200
    
        risk_free_rate = float(response.json().get('observations')[0].get('value'))  # most recent 10 yr TIPS rate
        risk_free_rate /= 100
        
        return risk_free_rate

    except AssertionError:
        return None


def get_market_risk_volatility():
    df = pd.read_excel('Data/shiller_data.xls', sheet_name='Data', skiprows=7)
    
    df = df.dropna(subset=['Date'])
    
    df['Monthly_Returns'] = df['Price'].pct_change()
        
    # Short-Horizon Volatility (last 3 months)
    short_horizon_volatility = df['Monthly_Returns'][-3:].std()

    # Long-Horizon Volatility (last 5 years)
    long_horizon_volatility = df['Monthly_Returns'][-60:].std()

    # Blend the volatilities with equal weighting (50% each) -> play around with weight parameters
    blended_volatility = (short_horizon_volatility + long_horizon_volatility) / 2

    return blended_volatility


@st.cache_data
def merton_share(risk_aversion):
    real_yield = 1 / get_shiller_pe_ratio()
    risk_free_rate = get_risk_free_rate()
    market_risk = get_market_risk_volatility()

    optimal_betting_fraction = (real_yield - risk_free_rate) / (risk_aversion * market_risk**2)

    return real_yield, risk_free_rate, market_risk, optimal_betting_fraction