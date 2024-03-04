import os
import pandas as pd
import polars as pl
import numpy as np
import requests
import streamlit as st
import xlrd


FRED_API_KEY = os.getenv('FRED_API_KEY')
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
# from config import FRED_API_KEY, RAPID_API_KEY
    

@st.cache_data
def get_price_history(ticker:str):
    url = "https://real-time-finance-data.p.rapidapi.com/stock-time-series"

    querystring = {"symbol":ticker,"period":"MAX","language":"en"}

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "real-time-finance-data.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    
    try:
        assert response.status_code == 200
        
        return response.json().get('data')['time_series']
        
    except AssertionError as e:
        st.error(e)
        st.stop()
    


@st.cache_data
def get_cpi_data(date_max):
    url = f'https://api.stlouisfed.org/fred/series/observations?series_id=CPILFESL&api_key={FRED_API_KEY}&file_type=json'
    response = requests.get(url)
    
    try:
        assert response.status_code == 200
    
        data = pd.DataFrame(response.json().get('observations'))
        data = data[['date', 'value']]
                
        data['date'] = pd.to_datetime(data.date)
        data['date'] = data.date.apply(lambda date: date.date())
        data['date'] = pd.to_datetime(data.date)
        data['value'] = data.value.astype(float)
        
        # Get latest record
        data = data.set_index('date')
        
        date_rng = pd.date_range(start=data.index.min().date(), end=date_max, freq='D')
        data = data.reindex(date_rng)
        data['value'] = data.value.fillna(method='ffill')
        
        data = data.reset_index()
        data.columns = ['Date', 'CPI']
        
        return data

    except AssertionError as e:
        st.error(e)
        st.stop()
    

@st.cache_data
def get_10yr_tips(date_max):
    # Param frequency (d default): d = Daily, w = Weekly, bw = Biweekly, m = Monthly, q = Quarterly, sa = Semiannual, a = Annual
    url = f'https://api.stlouisfed.org/fred/series/observations?series_id=DTP10J28&api_key={FRED_API_KEY}&frequency=d&sort_order=desc&file_type=json'
    response = requests.get(url)
    
    try:
        assert response.status_code == 200
        series = response.json().get('observations')
        
        dates = [record.get('date') for record in series]
        risk_free_rate_series = [record.get('value') for record in series]
        risk_free_rate_series = [float(value) if value != '.' else np.nan for value in risk_free_rate_series]
        
        data = pd.DataFrame({'Date': dates, 'TIPS_10yr': risk_free_rate_series})

        data['Date'] = pd.to_datetime(data.Date)
        data['Date'] = data.Date.apply(lambda date: date.date())
        data['Date'] = pd.to_datetime(data.Date)
        
        # Get latest record
        data = data.sort_values('Date')
        data = data.set_index('Date')
        date_rng = pd.date_range(start=data.index.min().date(), end=date_max, freq='D')
        data = data.reindex(date_rng)
        
        data['TIPS_10yr'] = data['TIPS_10yr'].fillna(method='ffill') / 100
    
        data = data.reset_index()
        data.columns = ['Date', 'TIPS_10yr']
                
        return data

    except AssertionError as e:
        st.error(e)
        st.stop()


@st.cache_data
def get_price_data(ticker):
    series_dict = get_price_history(ticker)
    
    dates = series_dict.keys()
    prices = [hash.get('price') for hash in series_dict.values()]

    df = pd.DataFrame({'Date': dates, 'Close': prices})
    df['Date'] = pd.to_datetime(df.Date)
    df['Date'] = df.Date.apply(lambda date: date.date())
    df['Date'] = pd.to_datetime(df.Date)

    df = df.drop_duplicates()
    df = df.set_index('Date')

    up_to_date = df.index.max().date()
    date_rng = pd.date_range(start=df.index.min().date(), end=up_to_date, freq='D')
    df = df.reindex(date_rng)

    df_interpolated = df.interpolate(method='linear')

    df_interpolated = df_interpolated.reset_index()
    df_interpolated.columns = ['Date', 'Close']
    
    return df_interpolated, up_to_date


@st.cache_data
def get_pe_data(date_max):
    pe_data = pl.read_csv('Data/sp-500-price-earnings-ra.csv')
    pe_data = pe_data.with_columns(pl.col('DateTime').str.strptime(pl.Datetime, format="%Y-%m-%d %H:%M:%S"))
    pe_data = pe_data.to_pandas()
    pe_data.columns = ['Date', 'PE_Ratio']
    
    # Get latest record
    pe_data = pe_data.set_index('Date')
    
    date_rng = pd.date_range(start=pe_data.index.min().date(), end=date_max, freq='D')
    pe_data = pe_data.reindex(date_rng)
    pe_data['PE_Ratio'] = pe_data['PE_Ratio'].fillna(method='ffill')
    
    pe_data = pe_data.reset_index()
    pe_data.columns = ['Date', 'PE_Ratio']
    
    return pe_data


def collect_data(ticker:str):
    
    price_df, up_to_date = get_price_data(ticker)
    cpi_df = get_cpi_data(up_to_date)
    pe_df = get_pe_data(up_to_date)
    tips_10yr = get_10yr_tips(up_to_date)
        
    data = price_df.merge(cpi_df, on='Date', how='left') \
        .merge(pe_df, on='Date', how='left') \
        .merge(tips_10yr, on='Date', how='left')
    
    return data


@st.cache_data
def prelim_calculations(df):
    copy_df = df.copy()
    try:
        copy_df['Date'] = pd.to_datetime(copy_df['Date'])    
        copy_df = copy_df.set_index('Date')
        
        copy_df['Real_Price'] = copy_df.Close / copy_df.CPI * copy_df.CPI.iloc[-1]
        copy_df['Earnings'] = copy_df.Close / copy_df.PE_Ratio
        copy_df['Real_Earnings'] = copy_df.Earnings / copy_df.CPI * copy_df.CPI.iloc[-1]
        copy_df['CAPE'] = copy_df.Real_Price / copy_df.Real_Earnings.rolling(window=30*12*10).mean()
        copy_df['Real_Yield'] = 1 / copy_df.CAPE
        
        monthly_df = copy_df[['Close']].resample('M').mean()  # Resample to monthly, forward fill any missing data
        copy_df['Monthly_Returns'] = monthly_df['Close'].pct_change()
        copy_df['Monthly_Returns'] = copy_df['Monthly_Returns'].fillna(method='ffill')
        
        # Short and long term market volatility (last 3 months and 5 years)
        copy_df['Market_Risk']= (copy_df.Monthly_Returns.rolling(window=90).std() + copy_df.Monthly_Returns.rolling(window=30*12*5).std()) / 2  
    
        return copy_df
    
    except TypeError as e:
        st.error(e)
        st.stop()


@st.cache_data
def merton_share(data, risk_aversion:int):
    copy_df = data.copy()
    copy_df['Optimal_Bet_Fraction'] = (copy_df.Real_Yield - copy_df.TIPS_10yr) / (risk_aversion * copy_df.Market_Risk**2)

    return copy_df


@st.cache_data
def update_risk(df, risk_aversion, longterm_weight):
    copy_df = df.copy()
    
    # Short and long term market volatility (last 3 months and 5 years)
    copy_df['Market_Risk']= (1-longterm_weight)*copy_df.Monthly_Returns.rolling(window=90).std() + longterm_weight*copy_df.Monthly_Returns.rolling(window=30*12*5).std()

    # Recalculate optimal bet fraction
    copy_df = merton_share(copy_df, risk_aversion)
    
    return copy_df