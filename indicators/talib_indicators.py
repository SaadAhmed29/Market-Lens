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

    def bbands(self, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands
        
        Args:
            timeperiod (int): Default 5.
            nbdevup (int): Default 2.
            nbdevdn (int): Default 2.
            matype (int): Default 0.
            
        Returns:
            tuple[pd.Series, pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df['close'].values
        upperband, middleband, lowerband = talib.BBANDS(
            close, timeperiod=timeperiod, nbdevup=nbdevup, nbdevdn=nbdevdn, matype=matype
        )
        return (pd.Series(upperband, index=self.df.index, name='bb_upperband'), 
                pd.Series(middleband, index=self.df.index, name='bb_middleband'), 
                pd.Series(lowerband, index=self.df.index, name='bb_lowerband'))

    def dema(self, timeperiod=30) -> pd.Series:
        """
        Double Exponential Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.DEMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='DEMA')

    def ema(self, timeperiod=30) -> pd.Series:
        """
        Exponential Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.EMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='EMA')

    def ht_trendline(self) -> pd.Series:
        """
        Hilbert Transform - Instantaneous Trendline
        
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.HT_TRENDLINE(close)
        return pd.Series(res, index=self.df.index, name='HT_TRENDLINE')

    def kama(self, timeperiod=30) -> pd.Series:
        """
        Kaufman Adaptive Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.KAMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='KAMA')

    def ma(self, timeperiod=30, matype=0) -> pd.Series:
        """
        Moving average
        
        Args:
            timeperiod (int): Default 30.
            matype (int): Default 0.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.MA(close, timeperiod=timeperiod, matype=matype)
        return pd.Series(res, index=self.df.index, name='MA')

    def mama(self, fastlimit=0.5, slowlimit=0.05) -> tuple[pd.Series, pd.Series]:
        """
        MESA Adaptive Moving Average
        
        Args:
            fastlimit (float): Default 0.5.
            slowlimit (float): Default 0.05.
            
        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df['close'].values
        mama, fama = talib.MAMA(close, fastlimit=fastlimit, slowlimit=slowlimit)
        return (pd.Series(mama, index=self.df.index, name='mama'), pd.Series(fama, index=self.df.index, name='fama'))

    def mavp(self, periods, minperiod=2, maxperiod=30, matype=0) -> pd.Series:
        """
        Moving average with variable period
        
        Args:
            periods: Parameter.
            minperiod (int): Default 2.
            maxperiod (int): Default 30.
            matype (int): Default 0.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        
        # Ensure periods is a numpy array of floats
        if isinstance(periods, (pd.Series, pd.DataFrame)):
            periods_array = periods.values
        else:
            periods_array = np.asarray(periods, dtype=float)
            
        res = talib.MAVP(close, periods=periods_array, minperiod=minperiod, maxperiod=maxperiod, matype=matype)
        return pd.Series(res, index=self.df.index, name='MAVP')

    def midpoint(self, timeperiod=14) -> pd.Series:
        """
        MidPoint over period
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.MIDPOINT(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MIDPOINT')

    def midprice(self, timeperiod=14) -> pd.Series:
        """
        MidPrice over period
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.MIDPRICE(high, low, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MIDPRICE')

    def sar(self, acceleration=0.02, maximum=0.2) -> pd.Series:
        """
        Parabolic SAR
        
        Args:
            acceleration (float): Default 0.02.
            maximum (float): Default 0.2.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.SAR(high, low, acceleration=acceleration, maximum=maximum)
        return pd.Series(res, index=self.df.index, name='SAR')

    def sarext(self, startvalue=0, offsetonreverse=0, accelerationinitlong=0.02, 
               accelerationlong=0.02, accelerationmaxlong=0.2, accelerationinitshort=0.02, 
               accelerationshort=0.02, accelerationmaxshort=0.2) -> pd.Series:
        """
        Parabolic SAR - Extended
        
        Args:
            startvalue (int): Default 0.
            offsetonreverse (int): Default 0.
            accelerationinitlong (float): Default 0.02.
            accelerationlong (float): Default 0.02.
            accelerationmaxlong (float): Default 0.2.
            accelerationinitshort (float): Default 0.02.
            accelerationshort (float): Default 0.02.
            accelerationmaxshort (float): Default 0.2.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
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
        """
        Simple Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.SMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='SMA')

    def t3(self, timeperiod=5, vfactor=0.7) -> pd.Series:
        """
        Triple Exponential Moving Average (T3)
        
        Args:
            timeperiod (int): Default 5.
            vfactor (float): Default 0.7.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.T3(close, timeperiod=timeperiod, vfactor=vfactor)
        return pd.Series(res, index=self.df.index, name='T3')

    def tema(self, timeperiod=30) -> pd.Series:
        """
        Triple Exponential Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.TEMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='TEMA')

    def trima(self, timeperiod=30) -> pd.Series:
        """
        Triangular Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.TRIMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='TRIMA')

    def wma(self, timeperiod=30) -> pd.Series:
        """
        Weighted Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.WMA(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='WMA')


    # MOMENTUM INDICATORS

    def adx(self, timeperiod=14) -> pd.Series:
        """
        Average Directional Movement Index
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.ADX(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ADX')

    def adxr(self, timeperiod=14) -> pd.Series:
        """
        Average Directional Movement Index Rating
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.ADXR(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ADXR')

    def apo(self, fastperiod=12, slowperiod=26, matype=0) -> pd.Series:
        """
        Absolute Price Oscillator
        
        Args:
            fastperiod (int): Default 12.
            slowperiod (int): Default 26.
            matype (int): Default 0.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.APO(close, fastperiod=fastperiod, slowperiod=slowperiod, matype=matype)
        return pd.Series(res, index=self.df.index, name='APO')

    def aroon(self, timeperiod=14) -> tuple[pd.Series, pd.Series]:
        """
        Aroon
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        aroondown, aroonup = talib.AROON(high, low, timeperiod=timeperiod)
        return (pd.Series(aroondown, index=self.df.index, name='aroondown'), pd.Series(aroonup, index=self.df.index, name='aroonup'))

    def aroonosc(self, timeperiod=14) -> pd.Series:
        """
        Aroon Oscillator
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.AROONOSC(high, low, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='AROONOSC')

    def bop(self) -> pd.Series:
        """
        Balance Of Power
        
        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_ = self.df['open'].values
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.BOP(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='BOP')

    def cci(self, timeperiod=14) -> pd.Series:
        """
        Commodity Channel Index
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.CCI(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='CCI')

    def cmo(self, timeperiod=14) -> pd.Series:
        """
        Chande Momentum Oscillator
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.CMO(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='CMO')

    def dx(self, timeperiod=14) -> pd.Series:
        """
        Directional Movement Index
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.DX(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='dx')

    def macd(self, fastperiod=12, slowperiod=26, signalperiod=9) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence/Divergence
        
        Args:
            fastperiod (int): Default 12.
            slowperiod (int): Default 26.
            signalperiod (int): Default 9.
            
        Returns:
            tuple[pd.Series, pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df['close'].values
        macd, macdsignal, macdhist = talib.MACD(close, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        return (pd.Series(macd, index=self.df.index, name='macd'), pd.Series(macdsignal, index=self.df.index, name='macd_signal'), pd.Series(macdhist, index=self.df.index, name='macd_hist'))

    def macdext(self, fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, signalperiod=9, signalmatype=0) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD with controllable MA type
        
        Args:
            fastperiod (int): Default 12.
            fastmatype (int): Default 0.
            slowperiod (int): Default 26.
            slowmatype (int): Default 0.
            signalperiod (int): Default 9.
            signalmatype (int): Default 0.
            
        Returns:
            tuple[pd.Series, pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df['close'].values
        macd, macdsignal, macdhist = talib.MACDEXT(close, fastperiod=fastperiod, fastmatype=fastmatype, slowperiod=slowperiod, slowmatype=slowmatype, signalperiod=signalperiod, signalmatype=signalmatype)
        return (pd.Series(macd, index=self.df.index, name='macdext_macd'), pd.Series(macdsignal, index=self.df.index, name='macdext_signal'), pd.Series(macdhist, index=self.df.index, name='macdext_hist'))

    def macdfix(self, signalperiod=9) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence/Divergence Fix 12/26
        
        Args:
            signalperiod (int): Default 9.
            
        Returns:
            tuple[pd.Series, pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df['close'].values
        macd, macdsignal, macdhist = talib.MACDFIX(close, signalperiod=signalperiod)
        return (pd.Series(macd, index=self.df.index, name='macdfix_macd'), pd.Series(macdsignal, index=self.df.index, name='macdfix_signal'), pd.Series(macdhist, index=self.df.index, name='macdfix_hist'))

    def mfi(self, timeperiod=14) -> pd.Series:
        """
        Money Flow Index
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        volume = self.df['volume'].values
        res = talib.MFI(high, low, close, volume, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MFI')

    def minus_di(self, timeperiod=14) -> pd.Series:
        """
        Minus Directional Indicator
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.MINUS_DI(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MINUS_DI')

    def minus_dm(self, timeperiod=14) -> pd.Series:
        """
        Minus Directional Movement
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.MINUS_DM(high, low, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MINUS_DM')

    def mom(self, timeperiod=10) -> pd.Series:
        """
        Momentum
        
        Args:
            timeperiod (int): Default 10.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.MOM(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MOM')

    def plus_di(self, timeperiod=14) -> pd.Series:
        """
        Plus Directional Indicator
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.PLUS_DI(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='PLUS_DI')

    def plus_dm(self, timeperiod=14) -> pd.Series:
        """
        Plus Directional Movement
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.PLUS_DM(high, low, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='PLUS_DM')

    def ppo(self, fastperiod=12, slowperiod=26, matype=0) -> pd.Series:
        """
        Percentage Price Oscillator
        
        Args:
            fastperiod (int): Default 12.
            slowperiod (int): Default 26.
            matype (int): Default 0.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.PPO(close, fastperiod=fastperiod, slowperiod=slowperiod, matype=matype)
        return pd.Series(res, index=self.df.index, name='PPO')

    def roc(self, timeperiod=10) -> pd.Series:
        """
        Rate of change : ((price/prevPrice)-1)*100
        
        Args:
            timeperiod (int): Default 10.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.ROC(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ROC')

    def rocp(self, timeperiod=10) -> pd.Series:
        """
        Rate of change Percentage: (price-prevPrice)/prevPrice
        
        Args:
            timeperiod (int): Default 10.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.ROCP(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ROCP')

    def rocr(self, timeperiod=10) -> pd.Series:
        """
        Rate of change ratio: (price/prevPrice)
        
        Args:
            timeperiod (int): Default 10.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.ROCR(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ROCR')

    def rocr100(self, timeperiod=10) -> pd.Series:
        """
        Rate of change ratio 100 scale: (price/prevPrice)*100
        
        Args:
            timeperiod (int): Default 10.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.ROCR100(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ROCR100')

    def rsi(self, timeperiod=14) -> pd.Series:
        """
        Relative Strength Index
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.RSI(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='RSI')

    def stoch(self, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0) -> tuple[pd.Series, pd.Series]:
        """
        Stochastic
        
        Args:
            fastk_period (int): Default 5.
            slowk_period (int): Default 3.
            slowk_matype (int): Default 0.
            slowd_period (int): Default 3.
            slowd_matype (int): Default 0.
            
        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        slowk, slowd = talib.STOCH(high, low, close, fastk_period=fastk_period, slowk_period=slowk_period, slowk_matype=slowk_matype, slowd_period=slowd_period, slowd_matype=slowd_matype)
        return (pd.Series(slowk, index=self.df.index, name='stoch_slowk'), pd.Series(slowd, index=self.df.index, name='stoch_slowd'))

    def stochf(self, fastk_period=5, fastd_period=3, fastd_matype=0) -> tuple[pd.Series, pd.Series]:
        """
        Stochastic Fast
        
        Args:
            fastk_period (int): Default 5.
            fastd_period (int): Default 3.
            fastd_matype (int): Default 0.
            
        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        fastk, fastd = talib.STOCHF(high, low, close, fastk_period=fastk_period, fastd_period=fastd_period, fastd_matype=fastd_matype)
        return (pd.Series(fastk, index=self.df.index, name='stochf_fastk'), pd.Series(fastd, index=self.df.index, name='stochf_fastd'))

    def stochrsi(self, timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0) -> tuple[pd.Series, pd.Series]:
        """
        Stochastic Relative Strength Index
        
        Args:
            timeperiod (int): Default 14.
            fastk_period (int): Default 5.
            fastd_period (int): Default 3.
            fastd_matype (int): Default 0.
            
        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df['close'].values
        fastk, fastd = talib.STOCHRSI(close, timeperiod=timeperiod, fastk_period=fastk_period, fastd_period=fastd_period, fastd_matype=fastd_matype)
        return (pd.Series(fastk, index=self.df.index, name='stochrsi_fastk'), pd.Series(fastd, index=self.df.index, name='stochrsi_fastd'))

    def trix(self, timeperiod=30) -> pd.Series:
        """
        1-day Rate-Of-Change (ROC) of a Triple Smooth EMA
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.TRIX(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='TRIX')

    def ultosc(self, timeperiod1=7, timeperiod2=14, timeperiod3=28) -> pd.Series:
        """
        Ultimate Oscillator
        
        Args:
            timeperiod1 (int): Default 7.
            timeperiod2 (int): Default 14.
            timeperiod3 (int): Default 28.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.ULTOSC(high, low, close, timeperiod1=timeperiod1, timeperiod2=timeperiod2, timeperiod3=timeperiod3)
        return pd.Series(res, index=self.df.index, name='ULTOSC')

    def willr(self, timeperiod=14) -> pd.Series:
        """
        Williams' %R
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.WILLR(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='WILLR')

    # VOLUME INDICATORS

    def ad(self) -> pd.Series:
        """
        Chaikin A/D Line

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        volume = self.df['volume'].values
        res = talib.AD(high, low, close, volume)
        return pd.Series(res, index=self.df.index, name='AD')

    def adosc(self, fastperiod=3, slowperiod=10) -> pd.Series:
        """
        Chaikin A/D Oscillator

        Args:
            fastperiod: Default 3.
            slowperiod: Default 10.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        volume = self.df['volume'].values
        res = talib.ADOSC(high, low, close, volume, fastperiod=fastperiod, slowperiod=slowperiod)
        return pd.Series(res, index=self.df.index, name='ADOSC')

    def obv(self) -> pd.Series:
        """
        On Balance Volume

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        volume = self.df['volume'].values
        res = talib.OBV(close, volume)
        return pd.Series(res, index=self.df.index, name='OBV')

    # CYCLE INDICATORS

    def ht_dcperiod(self) -> pd.Series:
        """
        Hilbert Transform - Dominant Cycle Period

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.HT_DCPERIOD(close)
        return pd.Series(res, index=self.df.index, name='HT_DCPERIOD')

    def ht_dcphase(self) -> pd.Series:
        """
        Hilbert Transform - Dominant Cycle Phase

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.HT_DCPHASE(close)
        return pd.Series(res, index=self.df.index, name='HT_DCPHASE')

    def ht_phasor(self) -> tuple[pd.Series, pd.Series]:
        """
        Hilbert Transform - Phasor Components

        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df['close'].values
        inphase, quadrature = talib.HT_PHASOR(close)
        return (pd.Series(inphase, index=self.df.index, name='inphase'), pd.Series(quadrature, index=self.df.index, name='quadrature'))

    def ht_sine(self) -> tuple[pd.Series, pd.Series]:
        """
        Hilbert Transform - SineWave

        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df['close'].values
        sine, leadsine = talib.HT_SINE(close)
        return (pd.Series(sine, index=self.df.index, name='sine'), pd.Series(leadsine, index=self.df.index, name='leadsine'))

    def ht_trendmode(self) -> pd.Series:
        """
        Hilbert Transform - Trend vs Cycle Mode

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.HT_TRENDMODE(close)
        return pd.Series(res, index=self.df.index, name='HT_TRENDMODE')

    # PRICE TRANSFORM

    def avgprice(self) -> pd.Series:
        """
        Average Price

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_ = self.df['open'].values
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.AVGPRICE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='AVGPRICE')

    def medprice(self) -> pd.Series:
        """
        Median Price

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.MEDPRICE(high, low)
        return pd.Series(res, index=self.df.index, name='MEDPRICE')

    def typprice(self) -> pd.Series:
        """
        Typical Price

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.TYPPRICE(high, low, close)
        return pd.Series(res, index=self.df.index, name='TYPPRICE')

    def wclprice(self) -> pd.Series:
        """
        Weighted Close Price

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.WCLPRICE(high, low, close)
        return pd.Series(res, index=self.df.index, name='WCLPRICE')

    # VOLATILITY INDICATORS

    def atr(self, timeperiod=14) -> pd.Series:
        """
        Average True Range

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.ATR(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ATR')

    def natr(self, timeperiod=14) -> pd.Series:
        """
        Normalized Average True Range

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.NATR(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='NATR')

    def trange(self) -> pd.Series:
        """
        True Range

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.TRANGE(high, low, close)
        return pd.Series(res, index=self.df.index, name='TRANGE')

    # STATISTIC FUNCTIONS

    def beta(self, timeperiod=5) -> pd.Series:
        """
        Beta

        Args:
            timeperiod: Default 5.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.BETA(high, low, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='BETA')

    def correl(self, timeperiod=30) -> pd.Series:
        """
        Pearson's Correlation Coefficient (r)

        Args:
            timeperiod: Default 30.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.CORREL(high, low, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='CORREL')

    def linearreg(self, timeperiod=14) -> pd.Series:
        """
        Linear Regression

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.LINEARREG(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='LINEARREG')

    def linearreg_angle(self, timeperiod=14) -> pd.Series:
        """
        Linear Regression Angle

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.LINEARREG_ANGLE(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='LINEARREG_ANGLE')

    def linearreg_intercept(self, timeperiod=14) -> pd.Series:
        """
        Linear Regression Intercept

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.LINEARREG_INTERCEPT(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='LINEARREG_INTERCEPT')

    def linearreg_slope(self, timeperiod=14) -> pd.Series:
        """
        Linear Regression Slope

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.LINEARREG_SLOPE(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='LINEARREG_SLOPE')

    def stddev(self, timeperiod=5, nbdev=1) -> pd.Series:
        """
        Standard Deviation

        Args:
            timeperiod: Default 5.
            nbdev: Default 1.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.STDDEV(close, timeperiod=timeperiod, nbdev=nbdev)
        return pd.Series(res, index=self.df.index, name='STDDEV')

    def tsf(self, timeperiod=14) -> pd.Series:
        """
        Time Series Forecast

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.TSF(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='TSF')

    def var(self, timeperiod=5, nbdev=1) -> pd.Series:
        """
        Variance

        Args:
            timeperiod: Default 5.
            nbdev: Default 1.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.VAR(close, timeperiod=timeperiod, nbdev=nbdev)
        return pd.Series(res, index=self.df.index, name='VAR')

    # MATH TRANSFORM

    def acos(self) -> pd.Series:
        """
        Vector Trigonometric ACos

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.ACOS(close)
        return pd.Series(res, index=self.df.index, name='ACOS')

    def asin(self) -> pd.Series:
        """
        Vector Trigonometric ASin

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.ASIN(close)
        return pd.Series(res, index=self.df.index, name='ASIN')

    def atan(self) -> pd.Series:
        """
        Vector Trigonometric ATan

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.ATAN(close)
        return pd.Series(res, index=self.df.index, name='ATAN')

    def ceil(self) -> pd.Series:
        """
        Vector Ceil

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.CEIL(close)
        return pd.Series(res, index=self.df.index, name='CEIL')

    def cos(self) -> pd.Series:
        """
        Vector Trigonometric Cos

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.COS(close)
        return pd.Series(res, index=self.df.index, name='COS')

    def cosh(self) -> pd.Series:
        """
        Vector Trigonometric Cosh

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.COSH(close)
        return pd.Series(res, index=self.df.index, name='COSH')

    def exp(self) -> pd.Series:
        """
        Vector Arithmetic Exp

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.EXP(close)
        return pd.Series(res, index=self.df.index, name='EXP')

    def floor(self) -> pd.Series:
        """
        Vector Floor

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.FLOOR(close)
        return pd.Series(res, index=self.df.index, name='FLOOR')

    def ln(self) -> pd.Series:
        """
        Vector Log Natural

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.LN(close)
        return pd.Series(res, index=self.df.index, name='LN')

    def log10(self) -> pd.Series:
        """
        Vector Log10

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.LOG10(close)
        return pd.Series(res, index=self.df.index, name='LOG10')

    def sin(self) -> pd.Series:
        """
        Vector Trigonometric Sin

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.SIN(close)
        return pd.Series(res, index=self.df.index, name='SIN')

    def sinh(self) -> pd.Series:
        """
        Vector Trigonometric Sinh

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.SINH(close)
        return pd.Series(res, index=self.df.index, name='SINH')

    def sqrt(self) -> pd.Series:
        """
        Vector Square Root

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.SQRT(close)
        return pd.Series(res, index=self.df.index, name='SQRT')

    def tan(self) -> pd.Series:
        """
        Vector Trigonometric Tan

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.TAN(close)
        return pd.Series(res, index=self.df.index, name='TAN')

    def tanh(self) -> pd.Series:
        """
        Vector Trigonometric Tanh

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.TANH(close)
        return pd.Series(res, index=self.df.index, name='TANH')

    # MATH OPERATORS

    def add(self) -> pd.Series:
        """
        Vector Arithmetic Add

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.ADD(high, low)
        return pd.Series(res, index=self.df.index, name='ADD')

    def div(self) -> pd.Series:
        """
        Vector Arithmetic Div

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.DIV(high, low)
        return pd.Series(res, index=self.df.index, name='DIV')

    def max(self, timeperiod=30) -> pd.Series:
        """
        Highest value over a specified period

        Args:
            timeperiod: Default 30.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.MAX(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MAX')

    def maxindex(self, timeperiod=30) -> pd.Series:
        """
        Index of highest value over a specified period

        Args:
            timeperiod: Default 30.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.MAXINDEX(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MAXINDEX')

    def min(self, timeperiod=30) -> pd.Series:
        """
        Lowest value over a specified period

        Args:
            timeperiod: Default 30.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.MIN(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MIN')

    def minindex(self, timeperiod=30) -> pd.Series:
        """
        Index of lowest value over a specified period

        Args:
            timeperiod: Default 30.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.MININDEX(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MININDEX')

    def minmax(self, timeperiod=30) -> tuple[pd.Series, pd.Series]:
        """
        Lowest and highest values over a specified period

        Args:
            timeperiod: Default 30.

        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df['close'].values
        min_val, max_val = talib.MINMAX(close, timeperiod=timeperiod)
        return (pd.Series(min_val, index=self.df.index, name='min'), pd.Series(max_val, index=self.df.index, name='max'))

    def minmaxindex(self, timeperiod=30) -> tuple[pd.Series, pd.Series]:
        """
        Indexes of lowest and highest values over a specified period

        Args:
            timeperiod: Default 30.

        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df['close'].values
        minidx, maxidx = talib.MINMAXINDEX(close, timeperiod=timeperiod)
        return (pd.Series(minidx, index=self.df.index, name='minidx'), pd.Series(maxidx, index=self.df.index, name='maxidx'))

    def mult(self) -> pd.Series:
        """
        Vector Arithmetic Mult

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.MULT(high, low)
        return pd.Series(res, index=self.df.index, name='MULT')

    def sub(self) -> pd.Series:
        """
        Vector Arithmetic Substraction

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.SUB(high, low)
        return pd.Series(res, index=self.df.index, name='SUB')

    def sum(self, timeperiod=30) -> pd.Series:
        """
        Summation

        Args:
            timeperiod: Default 30.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df['close'].values
        res = talib.SUM(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='SUM')

    # PATTERN RECOGNITION

    def cdl2crows(self) -> pd.Series:
        """
        Two Crows

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL2CROWS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL2CROWS')

    def cdl3blackcrows(self) -> pd.Series:
        """
        Three Black Crows

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL3BLACKCROWS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL3BLACKCROWS')

    def cdl3inside(self) -> pd.Series:
        """
        Three Inside Up/Down

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL3INSIDE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL3INSIDE')

    def cdl3linestrike(self) -> pd.Series:
        """
        Three-Line Strike

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL3LINESTRIKE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL3LINESTRIKE')

    def cdl3outside(self) -> pd.Series:
        """
        Three Outside Up/Down

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL3OUTSIDE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL3OUTSIDE')

    def cdl3starsinsouth(self) -> pd.Series:
        """
        Three Stars In The South

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL3STARSINSOUTH(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL3STARSINSOUTH')

    def cdl3whitesoldiers(self) -> pd.Series:
        """
        Three Advancing White Soldiers

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL3WHITESOLDIERS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL3WHITESOLDIERS')

    def cdlabandonedbaby(self, penetration=0.3) -> pd.Series:
        """
        Abandoned Baby

        Args:
            penetration: Default 0.3.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLABANDONEDBABY(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLABANDONEDBABY')

    def cdladvanceblock(self) -> pd.Series:
        """
        Advance Block

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLADVANCEBLOCK(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLADVANCEBLOCK')

    def cdlbelthold(self) -> pd.Series:
        """
        Belt-hold

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLBELTHOLD(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLBELTHOLD')

    def cdlbreakaway(self) -> pd.Series:
        """
        Breakaway

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLBREAKAWAY(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLBREAKAWAY')

    def cdlclosingmarubozu(self) -> pd.Series:
        """
        Closing Marubozu

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLCLOSINGMARUBOZU(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLCLOSINGMARUBOZU')

    def cdlconcealbabyswall(self) -> pd.Series:
        """
        Concealing Baby Swallow

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLCONCEALBABYSWALL(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLCONCEALBABYSWALL')

    def cdlcounterattack(self) -> pd.Series:
        """
        Counterattack

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLCOUNTERATTACK(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLCOUNTERATTACK')

    def cdldarkcloudcover(self, penetration=0.5) -> pd.Series:
        """
        Dark Cloud Cover

        Args:
            penetration: Default 0.5.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLDARKCLOUDCOVER(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLDARKCLOUDCOVER')

    def cdldoji(self) -> pd.Series:
        """
        Doji

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLDOJI(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLDOJI')

    def cdldojistar(self) -> pd.Series:
        """
        Doji Star

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLDOJISTAR(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLDOJISTAR')

    def cdldragonflydoji(self) -> pd.Series:
        """
        Dragonfly Doji

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLDRAGONFLYDOJI(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLDRAGONFLYDOJI')

    def cdlengulfing(self) -> pd.Series:
        """
        Engulfing Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLENGULFING(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLENGULFING')

    def cdleveningdojistar(self, penetration=0.3) -> pd.Series:
        """
        Evening Doji Star

        Args:
            penetration: Default 0.3.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLEVENINGDOJISTAR(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLEVENINGDOJISTAR')

    def cdleveningstar(self, penetration=0.3) -> pd.Series:
        """
        Evening Star

        Args:
            penetration: Default 0.3.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLEVENINGSTAR(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLEVENINGSTAR')

    def cdlgapsidesidewhite(self) -> pd.Series:
        """
        Up/Down-gap side-by-side white lines

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLGAPSIDESIDEWHITE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLGAPSIDESIDEWHITE')

    def cdlgravestonedoji(self) -> pd.Series:
        """
        Gravestone Doji

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLGRAVESTONEDOJI(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLGRAVESTONEDOJI')

    def cdlhammer(self) -> pd.Series:
        """
        Hammer

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHAMMER(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHAMMER')

    def cdlhangingman(self) -> pd.Series:
        """
        Hanging Man

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHANGINGMAN(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHANGINGMAN')

    def cdlharami(self) -> pd.Series:
        """
        Harami Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHARAMI(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHARAMI')

    def cdlharamicross(self) -> pd.Series:
        """
        Harami Cross Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHARAMICROSS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHARAMICROSS')

    def cdlhighwave(self) -> pd.Series:
        """
        High-Wave Candle

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHIGHWAVE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHIGHWAVE')

    def cdlhikkake(self) -> pd.Series:
        """
        Hikkake Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHIKKAKE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHIKKAKE')

    def cdlhikkakemod(self) -> pd.Series:
        """
        Modified Hikkake Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHIKKAKEMOD(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHIKKAKEMOD')

    def cdlhomingpigeon(self) -> pd.Series:
        """
        Homing Pigeon

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHOMINGPIGEON(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHOMINGPIGEON')

    def cdlidentical3crows(self) -> pd.Series:
        """
        Identical Three Crows

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLIDENTICAL3CROWS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLIDENTICAL3CROWS')

    def cdlinneck(self) -> pd.Series:
        """
        In-Neck Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLINNECK(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLINNECK')

    def cdlinvertedhammer(self) -> pd.Series:
        """
        Inverted Hammer

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLINVERTEDHAMMER(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLINVERTEDHAMMER')

    def cdlkicking(self) -> pd.Series:
        """
        Kicking

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLKICKING(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLKICKING')

    def cdlkickingbylength(self) -> pd.Series:
        """
        Kicking - bull/bear determined by the longer marubozu

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLKICKINGBYLENGTH(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLKICKINGBYLENGTH')

    def cdlladderbottom(self) -> pd.Series:
        """
        Ladder Bottom

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLLADDERBOTTOM(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLLADDERBOTTOM')

    def cdllongleggeddoji(self) -> pd.Series:
        """
        Long Legged Doji

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLLONGLEGGEDDOJI(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLLONGLEGGEDDOJI')

    def cdllongline(self) -> pd.Series:
        """
        Long Line Candle

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLLONGLINE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLLONGLINE')

    def cdlmarubozu(self) -> pd.Series:
        """
        Marubozu

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLMARUBOZU(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLMARUBOZU')

    def cdlmatchinglow(self) -> pd.Series:
        """
        Matching Low

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLMATCHINGLOW(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLMATCHINGLOW')

    def cdlmathold(self, penetration=0.5) -> pd.Series:
        """
        Mat Hold

        Args:
            penetration: Default 0.5.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLMATHOLD(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLMATHOLD')

    def cdlmorningdojistar(self, penetration=0.3) -> pd.Series:
        """
        Morning Doji Star

        Args:
            penetration: Default 0.3.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLMORNINGDOJISTAR(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLMORNINGDOJISTAR')

    def cdlmorningstar(self, penetration=0.3) -> pd.Series:
        """
        Morning Star

        Args:
            penetration: Default 0.3.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLMORNINGSTAR(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLMORNINGSTAR')

    def cdlonneck(self) -> pd.Series:
        """
        On-Neck Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLONNECK(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLONNECK')

    def cdlpiercing(self) -> pd.Series:
        """
        Piercing Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLPIERCING(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLPIERCING')

    def cdlrickshawman(self) -> pd.Series:
        """
        Rickshaw Man

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLRICKSHAWMAN(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLRICKSHAWMAN')

    def cdlrisefall3methods(self) -> pd.Series:
        """
        Rising/Falling Three Methods

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLRISEFALL3METHODS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLRISEFALL3METHODS')

    def cdlseparatinglines(self) -> pd.Series:
        """
        Separating Lines

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLSEPARATINGLINES(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLSEPARATINGLINES')

    def cdlshootingstar(self) -> pd.Series:
        """
        Shooting Star

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLSHOOTINGSTAR(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLSHOOTINGSTAR')

    def cdlshortline(self) -> pd.Series:
        """
        Short Line Candle

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLSHORTLINE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLSHORTLINE')

    def cdlspinningtop(self) -> pd.Series:
        """
        Spinning Top

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLSPINNINGTOP(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLSPINNINGTOP')

    def cdlstalledpattern(self) -> pd.Series:
        """
        Stalled Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLSTALLEDPATTERN(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLSTALLEDPATTERN')

    def cdlsticksandwich(self) -> pd.Series:
        """
        Stick Sandwich

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLSTICKSANDWICH(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLSTICKSANDWICH')

    def cdltakuri(self) -> pd.Series:
        """
        Takuri (Dragonfly Doji with very long lower shadow)

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLTAKURI(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLTAKURI')

    def cdltasukigap(self) -> pd.Series:
        """
        Tasuki Gap

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLTASUKIGAP(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLTASUKIGAP')

    def cdlthrusting(self) -> pd.Series:
        """
        Thrusting Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLTHRUSTING(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLTHRUSTING')

    def cdltristar(self) -> pd.Series:
        """
        Tristar Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLTRISTAR(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLTRISTAR')

    def cdlunique3river(self) -> pd.Series:
        """
        Unique 3 River

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLUNIQUE3RIVER(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLUNIQUE3RIVER')

    def cdlupsidegap2crows(self) -> pd.Series:
        """
        Upside Gap Two Crows

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLUPSIDEGAP2CROWS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLUPSIDEGAP2CROWS')

    def cdlxsidegap3methods(self) -> pd.Series:
        """
        Upside/Downside Gap Three Methods

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLXSIDEGAP3METHODS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLXSIDEGAP3METHODS')

    def get_indicators_df(self, *indicators, **kwargs) -> pd.DataFrame:
        """
        Computes multiple indicators and combines them with the original OHLCV data.
        Drops initial NaN rows (warm-up period of indicators) and shifts the
        dataframe by 1 to avoid lookahead bias.
        """
        import inspect
        df_combined = self.df.copy()
        
        for name in indicators:
            if not hasattr(self, name):
                continue
            
            method = getattr(self, name)
            sig = inspect.signature(method)
            valid_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
            
            result = method(**valid_kwargs)
            
            if isinstance(result, tuple):
                for series in result:
                    col_name = f"{series.name}"
                    df_combined[col_name] = series
            elif isinstance(result, pd.Series):
                col_name = f"{result.name}"
                df_combined[col_name] = result
        
        # Drop rows with NaN values (indicator warm-up period)
        df_combined = df_combined.dropna()
        
        # Shift by 1 to avoid lookahead bias
        df_combined = df_combined.shift(1).dropna()
        
        return df_combined

