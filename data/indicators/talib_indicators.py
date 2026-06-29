import numpy as np
import pandas as pd
import talib
from data.data_downloader import DataFetcher

class TalibIndicators:
    def __init__(self, exchange: str, symbol: str, start, end, time_frame: str):
        """
        Initializes the TalibIndicators class by fetching OHLCV data.
        """
        self.df, _ = DataFetcher.get_updated_df(
            exchange=exchange,
            symbol=symbol,
            start=start,
            end=end,
            time_frame=time_frame,
            resample_1m=False
        )

    def bbands(self, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0) -> pd.DataFrame:
        """Bollinger Bands"""
        close = self.df['close'].values
        upperband, middleband, lowerband = talib.BBANDS(
            close, timeperiod=timeperiod, nbdevup=nbdevup, nbdevdn=nbdevdn, matype=matype
        )
        return pd.DataFrame({
            'upperband': upperband, 
            'middleband': middleband, 
            'lowerband': lowerband
        }, index=self.df.index)

    def dema(self, timeperiod=30) -> pd.Series:
        """Double Exponential Moving Average"""
        close = self.df['close'].values
        res = talib.DEMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='DEMA')

    def ema(self, timeperiod=30) -> pd.Series:
        """Exponential Moving Average"""
        close = self.df['close'].values
        res = talib.EMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='EMA')

    def ht_trendline(self) -> pd.Series:
        """Hilbert Transform - Instantaneous Trendline"""
        close = self.df['close'].values
        res = talib.HT_TRENDLINE(close)
        return pd.Series(res, index=self.df.index, name='HT_TRENDLINE')

    def kama(self, timeperiod=30) -> pd.Series:
        """Kaufman Adaptive Moving Average"""
        close = self.df['close'].values
        res = talib.KAMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='KAMA')

    def ma(self, timeperiod=30, matype=0) -> pd.Series:
        """Moving average"""
        close = self.df['close'].values
        res = talib.MA(close, timeperiod=timeperiod, matype=matype)
        return pd.Series(res, index=self.df.index, name='MA')

    def mama(self, fastlimit=0.5, slowlimit=0.05) -> pd.DataFrame:
        """MESA Adaptive Moving Average"""
        close = self.df['close'].values
        mama, fama = talib.MAMA(close, fastlimit=fastlimit, slowlimit=slowlimit)
        return pd.DataFrame({'mama': mama, 'fama': fama}, index=self.df.index)

    def mavp(self, periods, minperiod=2, maxperiod=30, matype=0) -> pd.Series:
        """Moving average with variable period"""
        close = self.df['close'].values
        
        # Ensure periods is a numpy array of floats
        if isinstance(periods, (pd.Series, pd.DataFrame)):
            periods_array = periods.values
        else:
            periods_array = np.asarray(periods, dtype=float)
            
        res = talib.MAVP(close, periods=periods_array, minperiod=minperiod, maxperiod=maxperiod, matype=matype)
        return pd.Series(res, index=self.df.index, name='MAVP')

    def midpoint(self, timeperiod=14) -> pd.Series:
        """MidPoint over period"""
        close = self.df['close'].values
        res = talib.MIDPOINT(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MIDPOINT')

    def midprice(self, timeperiod=14) -> pd.Series:
        """MidPrice over period"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.MIDPRICE(high, low, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MIDPRICE')

    def sar(self, acceleration=0.02, maximum=0.2) -> pd.Series:
        """Parabolic SAR"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.SAR(high, low, acceleration=acceleration, maximum=maximum)
        return pd.Series(res, index=self.df.index, name='SAR')

    def sarext(self, startvalue=0, offsetonreverse=0, accelerationinitlong=0.02, 
               accelerationlong=0.02, accelerationmaxlong=0.2, accelerationinitshort=0.02, 
               accelerationshort=0.02, accelerationmaxshort=0.2) -> pd.Series:
        """Parabolic SAR - Extended"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.SAREXT(
            high, low, startvalue=startvalue, offsetonreverse=offsetonreverse, 
            accelerationinitlong=accelerationinitlong, accelerationlong=accelerationlong, 
            accelerationmaxlong=accelerationmaxlong, accelerationinitshort=accelerationinitshort, 
            accelerationshort=accelerationshort, accelerationmaxshort=accelerationmaxshort
        )
        return pd.Series(res, index=self.df.index, name='SAREXT')

    def sma(self, timeperiod=30) -> pd.Series:
        """Simple Moving Average"""
        close = self.df['close'].values
        res = talib.SMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='SMA')

    def t3(self, timeperiod=5, vfactor=0.7) -> pd.Series:
        """Triple Exponential Moving Average (T3)"""
        close = self.df['close'].values
        res = talib.T3(close, timeperiod=timeperiod, vfactor=vfactor)
        return pd.Series(res, index=self.df.index, name='T3')

    def tema(self, timeperiod=30) -> pd.Series:
        """Triple Exponential Moving Average"""
        close = self.df['close'].values
        res = talib.TEMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='TEMA')

    def trima(self, timeperiod=30) -> pd.Series:
        """Triangular Moving Average"""
        close = self.df['close'].values
        res = talib.TRIMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='TRIMA')

    def wma(self, timeperiod=30) -> pd.Series:
        """Weighted Moving Average"""
        close = self.df['close'].values
        res = talib.WMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='WMA')
