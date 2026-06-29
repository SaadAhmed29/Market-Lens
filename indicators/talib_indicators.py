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

    # OVERLAP STUDIES INDICATORS

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


    # MOMENTUM INDICATORS

    def adx(self, timeperiod=14) -> pd.Series:
        """Average Directional Movement Index"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.ADX(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ADX')

    def adxr(self, timeperiod=14) -> pd.Series:
        """Average Directional Movement Index Rating"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.ADXR(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ADXR')

    def apo(self, fastperiod=12, slowperiod=26, matype=0) -> pd.Series:
        """Absolute Price Oscillator"""
        close = self.df['close'].values
        res = talib.APO(close, fastperiod=fastperiod, slowperiod=slowperiod, matype=matype)
        return pd.Series(res, index=self.df.index, name='APO')

    def aroon(self, timeperiod=14) -> pd.DataFrame:
        """Aroon"""
        high = self.df['high'].values
        low = self.df['low'].values
        aroondown, aroonup = talib.AROON(high, low, timeperiod=timeperiod)
        return pd.DataFrame({'aroondown': aroondown, 'aroonup': aroonup}, index=self.df.index)

    def aroonosc(self, timeperiod=14) -> pd.Series:
        """Aroon Oscillator"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.AROONOSC(high, low, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='AROONOSC')

    def bop(self) -> pd.Series:
        """Balance Of Power"""
        open_ = self.df['open'].values
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.BOP(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='BOP')

    def cci(self, timeperiod=14) -> pd.Series:
        """Commodity Channel Index"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.CCI(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='CCI')

    def cmo(self, timeperiod=14) -> pd.Series:
        """Chande Momentum Oscillator"""
        close = self.df['close'].values
        res = talib.CMO(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='CMO')

    def dx(self, timeperiod=14) -> pd.Series:
        """Directional Movement Index"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.DX(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='DX')

    def macd(self, fastperiod=12, slowperiod=26, signalperiod=9) -> pd.DataFrame:
        """Moving Average Convergence/Divergence"""
        close = self.df['close'].values
        macd, macdsignal, macdhist = talib.MACD(close, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        return pd.DataFrame({'macd': macd, 'signal': macdsignal, 'hist': macdhist}, index=self.df.index)

    def macdext(self, fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, signalperiod=9, signalmatype=0) -> pd.DataFrame:
        """MACD with controllable MA type"""
        close = self.df['close'].values
        macd, macdsignal, macdhist = talib.MACDEXT(close, fastperiod=fastperiod, fastmatype=fastmatype, slowperiod=slowperiod, slowmatype=slowmatype, signalperiod=signalperiod, signalmatype=signalmatype)
        return pd.DataFrame({'macd': macd, 'signal': macdsignal, 'hist': macdhist}, index=self.df.index)

    def macdfix(self, signalperiod=9) -> pd.DataFrame:
        """Moving Average Convergence/Divergence Fix 12/26"""
        close = self.df['close'].values
        macd, macdsignal, macdhist = talib.MACDFIX(close, signalperiod=signalperiod)
        return pd.DataFrame({'macd': macd, 'signal': macdsignal, 'hist': macdhist}, index=self.df.index)

    def mfi(self, timeperiod=14) -> pd.Series:
        """Money Flow Index"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        volume = self.df['volume'].values
        res = talib.MFI(high, low, close, volume, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MFI')

    def minus_di(self, timeperiod=14) -> pd.Series:
        """Minus Directional Indicator"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.MINUS_DI(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MINUS_DI')

    def minus_dm(self, timeperiod=14) -> pd.Series:
        """Minus Directional Movement"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.MINUS_DM(high, low, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MINUS_DM')

    def mom(self, timeperiod=10) -> pd.Series:
        """Momentum"""
        close = self.df['close'].values
        res = talib.MOM(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MOM')

    def plus_di(self, timeperiod=14) -> pd.Series:
        """Plus Directional Indicator"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.PLUS_DI(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='PLUS_DI')

    def plus_dm(self, timeperiod=14) -> pd.Series:
        """Plus Directional Movement"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.PLUS_DM(high, low, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='PLUS_DM')

    def ppo(self, fastperiod=12, slowperiod=26, matype=0) -> pd.Series:
        """Percentage Price Oscillator"""
        close = self.df['close'].values
        res = talib.PPO(close, fastperiod=fastperiod, slowperiod=slowperiod, matype=matype)
        return pd.Series(res, index=self.df.index, name='PPO')

    def roc(self, timeperiod=10) -> pd.Series:
        """Rate of change : ((price/prevPrice)-1)*100"""
        close = self.df['close'].values
        res = talib.ROC(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ROC')

    def rocp(self, timeperiod=10) -> pd.Series:
        """Rate of change Percentage: (price-prevPrice)/prevPrice"""
        close = self.df['close'].values
        res = talib.ROCP(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ROCP')

    def rocr(self, timeperiod=10) -> pd.Series:
        """Rate of change ratio: (price/prevPrice)"""
        close = self.df['close'].values
        res = talib.ROCR(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ROCR')

    def rocr100(self, timeperiod=10) -> pd.Series:
        """Rate of change ratio 100 scale: (price/prevPrice)*100"""
        close = self.df['close'].values
        res = talib.ROCR100(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ROCR100')

    def rsi(self, timeperiod=14) -> pd.Series:
        """Relative Strength Index"""
        close = self.df['close'].values
        res = talib.RSI(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='RSI')

    def stoch(self, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0) -> pd.DataFrame:
        """Stochastic"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        slowk, slowd = talib.STOCH(high, low, close, fastk_period=fastk_period, slowk_period=slowk_period, slowk_matype=slowk_matype, slowd_period=slowd_period, slowd_matype=slowd_matype)
        return pd.DataFrame({'slowk': slowk, 'slowd': slowd}, index=self.df.index)

    def stochf(self, fastk_period=5, fastd_period=3, fastd_matype=0) -> pd.DataFrame:
        """Stochastic Fast"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        fastk, fastd = talib.STOCHF(high, low, close, fastk_period=fastk_period, fastd_period=fastd_period, fastd_matype=fastd_matype)
        return pd.DataFrame({'fastk': fastk, 'fastd': fastd}, index=self.df.index)

    def stochrsi(self, timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0) -> pd.DataFrame:
        """Stochastic Relative Strength Index"""
        close = self.df['close'].values
        fastk, fastd = talib.STOCHRSI(close, timeperiod=timeperiod, fastk_period=fastk_period, fastd_period=fastd_period, fastd_matype=fastd_matype)
        return pd.DataFrame({'fastk': fastk, 'fastd': fastd}, index=self.df.index)

    def trix(self, timeperiod=30) -> pd.Series:
        """1-day Rate-Of-Change (ROC) of a Triple Smooth EMA"""
        close = self.df['close'].values
        res = talib.TRIX(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='TRIX')

    def ultosc(self, timeperiod1=7, timeperiod2=14, timeperiod3=28) -> pd.Series:
        """Ultimate Oscillator"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.ULTOSC(high, low, close, timeperiod1=timeperiod1, timeperiod2=timeperiod2, timeperiod3=timeperiod3)
        return pd.Series(res, index=self.df.index, name='ULTOSC')

    def willr(self, timeperiod=14) -> pd.Series:
        """Williams' %R"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.WILLR(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='WILLR')
