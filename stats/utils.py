import pandas as pd

def ledger_to_returns(ledger_df: pd.DataFrame) -> pd.Series:
    """
    Converts a trade ledger DataFrame into a daily percentage returns Series
    with date_time as index, compatible with quantstats.
    """
    if ledger_df is None or ledger_df.empty:
        return pd.Series(dtype=float)
        
    df = ledger_df.copy()
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    
    # Sort by exit_time
    df = df.sort_values('exit_time')
    
    # Group by date and get the last balance of the day
    df['date'] = df['exit_time'].dt.floor('D')
    daily_balance = df.groupby('date')['balance_after_trade'].last()
    
    # Find initial balance
    first_trade = df.iloc[0]
    initial_balance = first_trade['balance_after_trade'] - first_trade['net_pnl']
    
    # Reindex to include all days between first and last trade
    start_date = df['date'].min()
    end_date = df['date'].max()
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    daily_balance = daily_balance.reindex(date_range).ffill()
    
    # Calculate daily percentage returns
    returns = daily_balance.pct_change()
    
    # For the first day, calculate return relative to the initial balance
    returns.iloc[0] = (daily_balance.iloc[0] - initial_balance) / initial_balance
    
    # Make timezone naive if necessary, quantstats often prefers it
    if returns.index.tz is not None:
        returns.index = returns.index.tz_localize(None)
        
    returns.index.name = 'Date'
    return returns
