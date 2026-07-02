import numpy as np
import pandas as pd
import talib
import yaml
from data.data_downloader import DataFetcher

class TalibIndicators:
    def __init__(self, exchange: str, symbol: str, start, end, time_frame: str, config_path: str):
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
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

    # OVERLAP STUDIES INDICATORS

    def bbands(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series, pd.Series]:
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
        close = self.df[inputs[0]].values
        upperband, middleband, lowerband = talib.BBANDS(close, **kwargs)
        return (pd.Series(upperband, index=self.df.index, name='bb_upperband'), 
                pd.Series(middleband, index=self.df.index, name='bb_middleband'), 
                pd.Series(lowerband, index=self.df.index, name='bb_lowerband'))

    def dema(self, inputs, **kwargs) -> pd.Series:
        """
        Double Exponential Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.DEMA(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='DEMA')

    def ema(self, inputs, **kwargs) -> pd.Series:
        """
        Exponential Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.EMA(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='EMA')

    def ht_trendline(self, inputs, **kwargs) -> pd.Series:
        """
        Hilbert Transform - Instantaneous Trendline
        
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.HT_TRENDLINE(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='HT_TRENDLINE')

    def kama(self, inputs, **kwargs) -> pd.Series:
        """
        Kaufman Adaptive Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.KAMA(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='KAMA')

    def ma(self, inputs, **kwargs) -> pd.Series:
        """
        Moving average
        
        Args:
            timeperiod (int): Default 30.
            matype (int): Default 0.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.MA(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='MA')

    def mama(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series]:
        """
        MESA Adaptive Moving Average
        
        Args:
            fastlimit (float): Default 0.5.
            slowlimit (float): Default 0.05.
            
        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        mama, fama = talib.MAMA(close, **kwargs)
        return (pd.Series(mama, index=self.df.index, name='mama'), pd.Series(fama, index=self.df.index, name='fama'))

    def mavp(self, inputs, **kwargs) -> pd.Series:
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
        close = self.df[inputs[0]].values

        periods = kwargs.pop('periods')  # extract from kwargs before passing remainder
        if isinstance(periods, (pd.Series, pd.DataFrame)):
            periods_array = periods.values.astype(float)
        else:
            periods_array = np.asarray(periods, dtype=float)
            
        res = talib.MAVP(close, periods_array, **kwargs)
        return pd.Series(res, index=self.df.index, name='MAVP')

    def midpoint(self, inputs, **kwargs) -> pd.Series:
        """
        MidPoint over period
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.MIDPOINT(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='MIDPOINT')

    def midprice(self, inputs, **kwargs) -> pd.Series:
        """
        MidPrice over period
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.MIDPRICE(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='MIDPRICE')

    def sar(self, inputs, **kwargs) -> pd.Series:
        """
        Parabolic SAR
        
        Args:
            acceleration (float): Default 0.02.
            maximum (float): Default 0.2.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.SAR(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='SAR')

    def sarext(self, inputs, **kwargs) -> pd.Series:
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
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.SAREXT(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='SAREXT')

    def sma(self, inputs, **kwargs) -> pd.Series:
        """
        Simple Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.SMA(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='SMA')

    def t3(self, inputs, **kwargs) -> pd.Series:
        """
        Triple Exponential Moving Average (T3)
        
        Args:
            timeperiod (int): Default 5.
            vfactor (float): Default 0.7.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.T3(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='T3')

    def tema(self, inputs, **kwargs) -> pd.Series:
        """
        Triple Exponential Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.TEMA(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='TEMA')

    def trima(self, inputs, **kwargs) -> pd.Series:
        """
        Triangular Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.TRIMA(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='TRIMA')

    def wma(self, inputs, **kwargs) -> pd.Series:
        """
        Weighted Moving Average
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.WMA(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='WMA')


    # MOMENTUM INDICATORS

    def adx(self, inputs, **kwargs) -> pd.Series:
        """
        Average Directional Movement Index
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.ADX(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='ADX')

    def adxr(self, inputs, **kwargs) -> pd.Series:
        """
        Average Directional Movement Index Rating
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.ADXR(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='ADXR')

    def apo(self, inputs, **kwargs) -> pd.Series:
        """
        Absolute Price Oscillator
        
        Args:
            fastperiod (int): Default 12.
            slowperiod (int): Default 26.
            matype (int): Default 0.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.APO(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='APO')

    def aroon(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series]:
        """
        Aroon
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        aroondown, aroonup = talib.AROON(high, low, **kwargs)
        return (pd.Series(aroondown, index=self.df.index, name='aroondown'), pd.Series(aroonup, index=self.df.index, name='aroonup'))

    def aroonosc(self, inputs, **kwargs) -> pd.Series:
        """
        Aroon Oscillator
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.AROONOSC(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='AROONOSC')

    def bop(self, inputs, **kwargs) -> pd.Series:
        """
        Balance Of Power
        
        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_ = self.df[inputs[0]].values
        high = self.df[inputs[1]].values
        low = self.df[inputs[2]].values
        close = self.df[inputs[3]].values
        res = talib.BOP(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='BOP')

    def cci(self, inputs, **kwargs) -> pd.Series:
        """
        Commodity Channel Index
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.CCI(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CCI')

    def cmo(self, inputs, **kwargs) -> pd.Series:
        """
        Chande Momentum Oscillator
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.CMO(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CMO')

    def dx(self, inputs, **kwargs) -> pd.Series:
        """
        Directional Movement Index
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.DX(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='dx')

    def macd(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence/Divergence
        
        Args:
            fastperiod (int): Default 12.
            slowperiod (int): Default 26.
            signalperiod (int): Default 9.
            
        Returns:
            tuple[pd.Series, pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        macd, macdsignal, macdhist = talib.MACD(close, **kwargs)
        return (pd.Series(macd, index=self.df.index, name='macd'), pd.Series(macdsignal, index=self.df.index, name='macd_signal'), pd.Series(macdhist, index=self.df.index, name='macd_hist'))

    def macdext(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series, pd.Series]:
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
        close = self.df[inputs[0]].values
        macd, macdsignal, macdhist = talib.MACDEXT(close, **kwargs)
        return (pd.Series(macd, index=self.df.index, name='macdext_macd'), pd.Series(macdsignal, index=self.df.index, name='macdext_signal'), pd.Series(macdhist, index=self.df.index, name='macdext_hist'))

    def macdfix(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence/Divergence Fix 12/26
        
        Args:
            signalperiod (int): Default 9.
            
        Returns:
            tuple[pd.Series, pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        macd, macdsignal, macdhist = talib.MACDFIX(close, **kwargs)
        return (pd.Series(macd, index=self.df.index, name='macdfix_macd'), pd.Series(macdsignal, index=self.df.index, name='macdfix_signal'), pd.Series(macdhist, index=self.df.index, name='macdfix_hist'))

    def mfi(self, inputs, **kwargs) -> pd.Series:
        """
        Money Flow Index
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        volume = self.df[inputs[3]].values
        res = talib.MFI(high, low, close, volume, **kwargs)
        return pd.Series(res, index=self.df.index, name='MFI')

    def minus_di(self, inputs, **kwargs) -> pd.Series:
        """
        Minus Directional Indicator
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.MINUS_DI(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='MINUS_DI')

    def minus_dm(self, inputs, **kwargs) -> pd.Series:
        """
        Minus Directional Movement
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.MINUS_DM(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='MINUS_DM')

    def mom(self, inputs, **kwargs) -> pd.Series:
        """
        Momentum
        
        Args:
            timeperiod (int): Default 10.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.MOM(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='MOM')

    def plus_di(self, inputs, **kwargs) -> pd.Series:
        """
        Plus Directional Indicator
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.PLUS_DI(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='PLUS_DI')

    def plus_dm(self, inputs, **kwargs) -> pd.Series:
        """
        Plus Directional Movement
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.PLUS_DM(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='PLUS_DM')

    def ppo(self, inputs, **kwargs) -> pd.Series:
        """
        Percentage Price Oscillator
        
        Args:
            fastperiod (int): Default 12.
            slowperiod (int): Default 26.
            matype (int): Default 0.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.PPO(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='PPO')

    def roc(self, inputs, **kwargs) -> pd.Series:
        """
        Rate of change : ((price/prevPrice)-1)*100
        
        Args:
            timeperiod (int): Default 10.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.ROC(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='ROC')

    def rocp(self, inputs, **kwargs) -> pd.Series:
        """
        Rate of change Percentage: (price-prevPrice)/prevPrice
        
        Args:
            timeperiod (int): Default 10.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.ROCP(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='ROCP')

    def rocr(self, inputs, **kwargs) -> pd.Series:
        """
        Rate of change ratio: (price/prevPrice)
        
        Args:
            timeperiod (int): Default 10.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.ROCR(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='ROCR')

    def rocr100(self, inputs, **kwargs) -> pd.Series:
        """
        Rate of change ratio 100 scale: (price/prevPrice)*100
        
        Args:
            timeperiod (int): Default 10.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.ROCR100(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='ROCR100')

    def rsi(self, inputs, **kwargs) -> pd.Series:
        """
        Relative Strength Index
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.RSI(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='RSI')

    def stoch(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series]:
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
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        slowk, slowd = talib.STOCH(high, low, close, **kwargs)
        return (pd.Series(slowk, index=self.df.index, name='stoch_slowk'), pd.Series(slowd, index=self.df.index, name='stoch_slowd'))

    def stochf(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series]:
        """
        Stochastic Fast
        
        Args:
            fastk_period (int): Default 5.
            fastd_period (int): Default 3.
            fastd_matype (int): Default 0.
            
        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        fastk, fastd = talib.STOCHF(high, low, close, **kwargs)
        return (pd.Series(fastk, index=self.df.index, name='stochf_fastk'), pd.Series(fastd, index=self.df.index, name='stochf_fastd'))

    def stochrsi(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series]:
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
        close = self.df[inputs[0]].values
        fastk, fastd = talib.STOCHRSI(close, **kwargs)
        return (pd.Series(fastk, index=self.df.index, name='stochrsi_fastk'), pd.Series(fastd, index=self.df.index, name='stochrsi_fastd'))

    def trix(self, inputs, **kwargs) -> pd.Series:
        """
        1-day Rate-Of-Change (ROC) of a Triple Smooth EMA
        
        Args:
            timeperiod (int): Default 30.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.TRIX(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='TRIX')

    def ultosc(self, inputs, **kwargs) -> pd.Series:
        """
        Ultimate Oscillator
        
        Args:
            timeperiod1 (int): Default 7.
            timeperiod2 (int): Default 14.
            timeperiod3 (int): Default 28.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.ULTOSC(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='ULTOSC')

    def willr(self, inputs, **kwargs) -> pd.Series:
        """
        Williams' %R
        
        Args:
            timeperiod (int): Default 14.
            
        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.WILLR(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='WILLR')

    # VOLUME INDICATORS

    def ad(self, inputs, **kwargs) -> pd.Series:
        """
        Chaikin A/D Line

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        volume = self.df[inputs[3]].values
        res = talib.AD(high, low, close, volume, **kwargs)
        return pd.Series(res, index=self.df.index, name='AD')

    def adosc(self, inputs, **kwargs) -> pd.Series:
        """
        Chaikin A/D Oscillator

        Args:
            fastperiod: Default 3.
            slowperiod: Default 10.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        volume = self.df[inputs[3]].values
        res = talib.ADOSC(high, low, close, volume, **kwargs)
        return pd.Series(res, index=self.df.index, name='ADOSC')

    def obv(self, inputs, **kwargs) -> pd.Series:
        """
        On Balance Volume

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        volume = self.df[inputs[1]].values
        res = talib.OBV(close, volume, **kwargs)
        return pd.Series(res, index=self.df.index, name='OBV')

    # CYCLE INDICATORS

    def ht_dcperiod(self, inputs, **kwargs) -> pd.Series:
        """
        Hilbert Transform - Dominant Cycle Period

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.HT_DCPERIOD(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='HT_DCPERIOD')

    def ht_dcphase(self, inputs, **kwargs) -> pd.Series:
        """
        Hilbert Transform - Dominant Cycle Phase

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.HT_DCPHASE(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='HT_DCPHASE')

    def ht_phasor(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series]:
        """
        Hilbert Transform - Phasor Components

        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        inphase, quadrature = talib.HT_PHASOR(close, **kwargs)
        return (pd.Series(inphase, index=self.df.index, name='inphase'), pd.Series(quadrature, index=self.df.index, name='quadrature'))

    def ht_sine(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series]:
        """
        Hilbert Transform - SineWave

        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        sine, leadsine = talib.HT_SINE(close, **kwargs)
        return (pd.Series(sine, index=self.df.index, name='sine'), pd.Series(leadsine, index=self.df.index, name='leadsine'))

    def ht_trendmode(self, inputs, **kwargs) -> pd.Series:
        """
        Hilbert Transform - Trend vs Cycle Mode

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.HT_TRENDMODE(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='HT_TRENDMODE')

    # PRICE TRANSFORM

    def avgprice(self, inputs, **kwargs) -> pd.Series:
        """
        Average Price

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_ = self.df[inputs[0]].values
        high = self.df[inputs[1]].values
        low = self.df[inputs[2]].values
        close = self.df[inputs[3]].values
        res = talib.AVGPRICE(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='AVGPRICE')

    def medprice(self, inputs, **kwargs) -> pd.Series:
        """
        Median Price

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.MEDPRICE(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='MEDPRICE')

    def typprice(self, inputs, **kwargs) -> pd.Series:
        """
        Typical Price

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.TYPPRICE(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='TYPPRICE')

    def wclprice(self, inputs, **kwargs) -> pd.Series:
        """
        Weighted Close Price

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.WCLPRICE(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='WCLPRICE')

    # VOLATILITY INDICATORS

    def atr(self, inputs, **kwargs) -> pd.Series:
        """
        Average True Range

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.ATR(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='ATR')

    def natr(self, inputs, **kwargs) -> pd.Series:
        """
        Normalized Average True Range

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.NATR(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='NATR')

    def trange(self, inputs, **kwargs) -> pd.Series:
        """
        True Range

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        close = self.df[inputs[2]].values
        res = talib.TRANGE(high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='TRANGE')

    # STATISTIC FUNCTIONS

    def beta(self, inputs, **kwargs) -> pd.Series:
        """
        Beta

        Args:
            timeperiod: Default 5.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.BETA(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='BETA')

    def correl(self, inputs, **kwargs) -> pd.Series:
        """
        Pearson's Correlation Coefficient (r)

        Args:
            timeperiod: Default 30.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.CORREL(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='CORREL')

    def linearreg(self, inputs, **kwargs) -> pd.Series:
        """
        Linear Regression

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.LINEARREG(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='LINEARREG')

    def linearreg_angle(self, inputs, **kwargs) -> pd.Series:
        """
        Linear Regression Angle

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.LINEARREG_ANGLE(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='LINEARREG_ANGLE')

    def linearreg_intercept(self, inputs, **kwargs) -> pd.Series:
        """
        Linear Regression Intercept

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.LINEARREG_INTERCEPT(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='LINEARREG_INTERCEPT')

    def linearreg_slope(self, inputs, **kwargs) -> pd.Series:
        """
        Linear Regression Slope

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.LINEARREG_SLOPE(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='LINEARREG_SLOPE')

    def stddev(self, inputs, **kwargs) -> pd.Series:
        """
        Standard Deviation

        Args:
            timeperiod: Default 5.
            nbdev: Default 1.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.STDDEV(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='STDDEV')

    def tsf(self, inputs, **kwargs) -> pd.Series:
        """
        Time Series Forecast

        Args:
            timeperiod: Default 14.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.TSF(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='TSF')

    def var(self, inputs, **kwargs) -> pd.Series:
        """
        Variance

        Args:
            timeperiod: Default 5.
            nbdev: Default 1.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.VAR(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='VAR')

    # MATH TRANSFORM

    def acos(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Trigonometric ACos

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.ACOS(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='ACOS')

    def asin(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Trigonometric ASin

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.ASIN(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='ASIN')

    def atan(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Trigonometric ATan

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.ATAN(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='ATAN')

    def ceil(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Ceil

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.CEIL(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CEIL')

    def cos(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Trigonometric Cos

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.COS(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='COS')

    def cosh(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Trigonometric Cosh

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.COSH(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='COSH')

    def exp(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Arithmetic Exp

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.EXP(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='EXP')

    def floor(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Floor

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.FLOOR(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='FLOOR')

    def ln(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Log Natural

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.LN(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='LN')

    def log10(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Log10

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.LOG10(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='LOG10')

    def sin(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Trigonometric Sin

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.SIN(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='SIN')

    def sinh(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Trigonometric Sinh

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.SINH(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='SINH')

    def sqrt(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Square Root

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.SQRT(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='SQRT')

    def tan(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Trigonometric Tan

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.TAN(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='TAN')

    def tanh(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Trigonometric Tanh

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.TANH(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='TANH')

    # MATH OPERATORS

    def add(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Arithmetic Add

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.ADD(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='ADD')

    def div(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Arithmetic Div

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.DIV(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='DIV')

    def max(self, inputs, **kwargs) -> pd.Series:
        """
        Highest value over a specified period

        Args:
            timeperiod: Default 30.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.MAX(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='MAX')

    def maxindex(self, inputs, **kwargs) -> pd.Series:
        """
        Index of highest value over a specified period

        Args:
            timeperiod: Default 30.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.MAXINDEX(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='MAXINDEX')

    def min(self, inputs, **kwargs) -> pd.Series:
        """
        Lowest value over a specified period

        Args:
            timeperiod: Default 30.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.MIN(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='MIN')

    def minindex(self, inputs, **kwargs) -> pd.Series:
        """
        Index of lowest value over a specified period

        Args:
            timeperiod: Default 30.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.MININDEX(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='MININDEX')

    def minmax(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series]:
        """
        Lowest and highest values over a specified period

        Args:
            timeperiod: Default 30.

        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        min_val, max_val = talib.MINMAX(close, **kwargs)
        return (pd.Series(min_val, index=self.df.index, name='min'), pd.Series(max_val, index=self.df.index, name='max'))

    def minmaxindex(self, inputs, **kwargs) -> tuple[pd.Series, pd.Series]:
        """
        Indexes of lowest and highest values over a specified period

        Args:
            timeperiod: Default 30.

        Returns:
            tuple[pd.Series, pd.Series]: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        minidx, maxidx = talib.MINMAXINDEX(close, **kwargs)
        return (pd.Series(minidx, index=self.df.index, name='minidx'), pd.Series(maxidx, index=self.df.index, name='maxidx'))

    def mult(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Arithmetic Mult

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.MULT(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='MULT')

    def sub(self, inputs, **kwargs) -> pd.Series:
        """
        Vector Arithmetic Substraction

        Returns:
            pd.Series: The calculated indicator(s).
        """
        high = self.df[inputs[0]].values
        low = self.df[inputs[1]].values
        res = talib.SUB(high, low, **kwargs)
        return pd.Series(res, index=self.df.index, name='SUB')

    def sum(self, inputs, **kwargs) -> pd.Series:
        """
        Summation

        Args:
            timeperiod: Default 30.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        close = self.df[inputs[0]].values
        res = talib.SUM(close, **kwargs)
        return pd.Series(res, index=self.df.index, name='SUM')

    # PATTERN RECOGNITION

    def cdl2crows(self, inputs, **kwargs) -> pd.Series:
        """
        Two Crows

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDL2CROWS(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDL2CROWS')

    def cdl3blackcrows(self, inputs, **kwargs) -> pd.Series:
        """
        Three Black Crows

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDL3BLACKCROWS(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDL3BLACKCROWS')

    def cdl3inside(self, inputs, **kwargs) -> pd.Series:
        """
        Three Inside Up/Down

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDL3INSIDE(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDL3INSIDE')

    def cdl3linestrike(self, inputs, **kwargs) -> pd.Series:
        """
        Three-Line Strike

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDL3LINESTRIKE(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDL3LINESTRIKE')

    def cdl3outside(self, inputs, **kwargs) -> pd.Series:
        """
        Three Outside Up/Down

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDL3OUTSIDE(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDL3OUTSIDE')

    def cdl3starsinsouth(self, inputs, **kwargs) -> pd.Series:
        """
        Three Stars In The South

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDL3STARSINSOUTH(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDL3STARSINSOUTH')

    def cdl3whitesoldiers(self, inputs, **kwargs) -> pd.Series:
        """
        Three Advancing White Soldiers

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDL3WHITESOLDIERS(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDL3WHITESOLDIERS')

    def cdlabandonedbaby(self, inputs, **kwargs) -> pd.Series:
        """
        Abandoned Baby

        Args:
            penetration: Default 0.3.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLABANDONEDBABY(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLABANDONEDBABY')

    def cdladvanceblock(self, inputs, **kwargs) -> pd.Series:
        """
        Advance Block

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLADVANCEBLOCK(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLADVANCEBLOCK')

    def cdlbelthold(self, inputs, **kwargs) -> pd.Series:
        """
        Belt-hold

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLBELTHOLD(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLBELTHOLD')

    def cdlbreakaway(self, inputs, **kwargs) -> pd.Series:
        """
        Breakaway

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLBREAKAWAY(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLBREAKAWAY')

    def cdlclosingmarubozu(self, inputs, **kwargs) -> pd.Series:
        """
        Closing Marubozu

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLCLOSINGMARUBOZU(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLCLOSINGMARUBOZU')

    def cdlconcealbabyswall(self, inputs, **kwargs) -> pd.Series:
        """
        Concealing Baby Swallow

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLCONCEALBABYSWALL(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLCONCEALBABYSWALL')

    def cdlcounterattack(self, inputs, **kwargs) -> pd.Series:
        """
        Counterattack

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLCOUNTERATTACK(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLCOUNTERATTACK')

    def cdldarkcloudcover(self, inputs, **kwargs) -> pd.Series:
        """
        Dark Cloud Cover

        Args:
            penetration: Default 0.5.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLDARKCLOUDCOVER(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLDARKCLOUDCOVER')

    def cdldoji(self, inputs, **kwargs) -> pd.Series:
        """
        Doji

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLDOJI(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLDOJI')

    def cdldojistar(self, inputs, **kwargs) -> pd.Series:
        """
        Doji Star

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLDOJISTAR(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLDOJISTAR')

    def cdldragonflydoji(self, inputs, **kwargs) -> pd.Series:
        """
        Dragonfly Doji

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLDRAGONFLYDOJI(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLDRAGONFLYDOJI')

    def cdlengulfing(self, inputs, **kwargs) -> pd.Series:
        """
        Engulfing Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLENGULFING(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLENGULFING')

    def cdleveningdojistar(self, inputs, **kwargs) -> pd.Series:
        """
        Evening Doji Star

        Args:
            penetration: Default 0.3.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLEVENINGDOJISTAR(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLEVENINGDOJISTAR')

    def cdleveningstar(self, inputs, **kwargs) -> pd.Series:
        """
        Evening Star

        Args:
            penetration: Default 0.3.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLEVENINGSTAR(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLEVENINGSTAR')

    def cdlgapsidesidewhite(self, inputs, **kwargs) -> pd.Series:
        """
        Up/Down-gap side-by-side white lines

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLGAPSIDESIDEWHITE(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLGAPSIDESIDEWHITE')

    def cdlgravestonedoji(self, inputs, **kwargs) -> pd.Series:
        """
        Gravestone Doji

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLGRAVESTONEDOJI(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLGRAVESTONEDOJI')

    def cdlhammer(self, inputs, **kwargs) -> pd.Series:
        """
        Hammer

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLHAMMER(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLHAMMER')

    def cdlhangingman(self, inputs, **kwargs) -> pd.Series:
        """
        Hanging Man

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLHANGINGMAN(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLHANGINGMAN')

    def cdlharami(self, inputs, **kwargs) -> pd.Series:
        """
        Harami Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLHARAMI(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLHARAMI')

    def cdlharamicross(self, inputs, **kwargs) -> pd.Series:
        """
        Harami Cross Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLHARAMICROSS(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLHARAMICROSS')

    def cdlhighwave(self, inputs, **kwargs) -> pd.Series:
        """
        High-Wave Candle

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLHIGHWAVE(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLHIGHWAVE')

    def cdlhikkake(self, inputs, **kwargs) -> pd.Series:
        """
        Hikkake Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLHIKKAKE(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLHIKKAKE')

    def cdlhikkakemod(self, inputs, **kwargs) -> pd.Series:
        """
        Modified Hikkake Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLHIKKAKEMOD(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLHIKKAKEMOD')

    def cdlhomingpigeon(self, inputs, **kwargs) -> pd.Series:
        """
        Homing Pigeon

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLHOMINGPIGEON(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLHOMINGPIGEON')

    def cdlidentical3crows(self, inputs, **kwargs) -> pd.Series:
        """
        Identical Three Crows

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLIDENTICAL3CROWS(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLIDENTICAL3CROWS')

    def cdlinneck(self, inputs, **kwargs) -> pd.Series:
        """
        In-Neck Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLINNECK(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLINNECK')

    def cdlinvertedhammer(self, inputs, **kwargs) -> pd.Series:
        """
        Inverted Hammer

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLINVERTEDHAMMER(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLINVERTEDHAMMER')

    def cdlkicking(self, inputs, **kwargs) -> pd.Series:
        """
        Kicking

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLKICKING(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLKICKING')

    def cdlkickingbylength(self, inputs, **kwargs) -> pd.Series:
        """
        Kicking - bull/bear determined by the longer marubozu

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLKICKINGBYLENGTH(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLKICKINGBYLENGTH')

    def cdlladderbottom(self, inputs, **kwargs) -> pd.Series:
        """
        Ladder Bottom

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLLADDERBOTTOM(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLLADDERBOTTOM')

    def cdllongleggeddoji(self, inputs, **kwargs) -> pd.Series:
        """
        Long Legged Doji

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLLONGLEGGEDDOJI(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLLONGLEGGEDDOJI')

    def cdllongline(self, inputs, **kwargs) -> pd.Series:
        """
        Long Line Candle

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLLONGLINE(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLLONGLINE')

    def cdlmarubozu(self, inputs, **kwargs) -> pd.Series:
        """
        Marubozu

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLMARUBOZU(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLMARUBOZU')

    def cdlmatchinglow(self, inputs, **kwargs) -> pd.Series:
        """
        Matching Low

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLMATCHINGLOW(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLMATCHINGLOW')

    def cdlmathold(self, inputs, **kwargs) -> pd.Series:
        """
        Mat Hold

        Args:
            penetration: Default 0.5.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLMATHOLD(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLMATHOLD')

    def cdlmorningdojistar(self, inputs, **kwargs) -> pd.Series:
        """
        Morning Doji Star

        Args:
            penetration: Default 0.3.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLMORNINGDOJISTAR(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLMORNINGDOJISTAR')

    def cdlmorningstar(self, inputs, **kwargs) -> pd.Series:
        """
        Morning Star

        Args:
            penetration: Default 0.3.

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLMORNINGSTAR(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLMORNINGSTAR')

    def cdlonneck(self, inputs, **kwargs) -> pd.Series:
        """
        On-Neck Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLONNECK(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLONNECK')

    def cdlpiercing(self, inputs, **kwargs) -> pd.Series:
        """
        Piercing Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLPIERCING(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLPIERCING')

    def cdlrickshawman(self, inputs, **kwargs) -> pd.Series:
        """
        Rickshaw Man

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLRICKSHAWMAN(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLRICKSHAWMAN')

    def cdlrisefall3methods(self, inputs, **kwargs) -> pd.Series:
        """
        Rising/Falling Three Methods

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLRISEFALL3METHODS(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLRISEFALL3METHODS')

    def cdlseparatinglines(self, inputs, **kwargs) -> pd.Series:
        """
        Separating Lines

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLSEPARATINGLINES(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLSEPARATINGLINES')

    def cdlshootingstar(self, inputs, **kwargs) -> pd.Series:
        """
        Shooting Star

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLSHOOTINGSTAR(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLSHOOTINGSTAR')

    def cdlshortline(self, inputs, **kwargs) -> pd.Series:
        """
        Short Line Candle

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLSHORTLINE(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLSHORTLINE')

    def cdlspinningtop(self, inputs, **kwargs) -> pd.Series:
        """
        Spinning Top

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLSPINNINGTOP(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLSPINNINGTOP')

    def cdlstalledpattern(self, inputs, **kwargs) -> pd.Series:
        """
        Stalled Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLSTALLEDPATTERN(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLSTALLEDPATTERN')

    def cdlsticksandwich(self, inputs, **kwargs) -> pd.Series:
        """
        Stick Sandwich

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLSTICKSANDWICH(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLSTICKSANDWICH')

    def cdltakuri(self, inputs, **kwargs) -> pd.Series:
        """
        Takuri (Dragonfly Doji with very long lower shadow)

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLTAKURI(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLTAKURI')

    def cdltasukigap(self, inputs, **kwargs) -> pd.Series:
        """
        Tasuki Gap

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLTASUKIGAP(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLTASUKIGAP')

    def cdlthrusting(self, inputs, **kwargs) -> pd.Series:
        """
        Thrusting Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLTHRUSTING(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLTHRUSTING')

    def cdltristar(self, inputs, **kwargs) -> pd.Series:
        """
        Tristar Pattern

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLTRISTAR(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLTRISTAR')

    def cdlunique3river(self, inputs, **kwargs) -> pd.Series:
        """
        Unique 3 River

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLUNIQUE3RIVER(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLUNIQUE3RIVER')

    def cdlupsidegap2crows(self, inputs, **kwargs) -> pd.Series:
        """
        Upside Gap Two Crows

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLUPSIDEGAP2CROWS(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLUPSIDEGAP2CROWS')

    def cdlxsidegap3methods(self, inputs, **kwargs) -> pd.Series:
        """
        Upside/Downside Gap Three Methods

        Returns:
            pd.Series: The calculated indicator(s).
        """
        open_, high, low, close = self.df[inputs[0]].values, self.df[inputs[1]].values, self.df[inputs[2]].values, self.df[inputs[3]].values
        res = talib.CDLXSIDEGAP3METHODS(open_, high, low, close, **kwargs)
        return pd.Series(res, index=self.df.index, name='CDLXSIDEGAP3METHODS')

    def get_indicators_df(self, indicator_list: list[str]) -> pd.DataFrame:
        """
        Computes multiple indicators defined in config and combines them with original OHLCV data.
        Drops initial NaN rows (warm-up period of indicators) and shifts only the
        indicator columns by 1 to avoid lookahead bias, while keeping OHLCV aligned
        with their true timestamp.
        """
        df_combined = self.df.copy()
        indicator_cols = []
        
        for ind_name in indicator_list:
            if ind_name not in self.config:
                print(f"Warning: Indicator {ind_name} not found in config.")
                continue
                
            configs = self.config[ind_name]
            for cfg in configs:
                inputs = cfg.get('inputs', [])
                parameters = cfg.get('parameters', {})
                aliases = cfg.get('aliases', {})
                
                if not aliases:
                    continue
                    
                method_name = ind_name.lower()
                    
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    result = method(inputs=inputs, **parameters)
                    
                    if isinstance(result, tuple):
                        alias_values = list(aliases.values())
                        for i, series in enumerate(result):
                            col_name = alias_values[i] if i < len(alias_values) else series.name
                            df_combined[col_name] = series
                            indicator_cols.append(col_name)
                    elif isinstance(result, pd.Series):
                        alias_values = list(aliases.values())
                        col_name = alias_values[0] if alias_values else result.name
                        df_combined[col_name] = result
                        indicator_cols.append(col_name)
        
        # Shift only the indicator columns to avoid lookahead bias
        if indicator_cols:
            df_combined[indicator_cols] = df_combined[indicator_cols].shift(1)
        
        # Drop rows with NaN values (indicator warm-up period + the shift-induced NaN row)
        #df_combined = df_combined.dropna()
        
        return df_combined
