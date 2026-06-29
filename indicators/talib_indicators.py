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

    # VOLUME INDICATORS

    def ad(self) -> pd.Series:
        """Chaikin A/D Line"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        volume = self.df['volume'].values
        res = talib.AD(high, low, close, volume)
        return pd.Series(res, index=self.df.index, name='AD')

    def adosc(self, fastperiod=3, slowperiod=10) -> pd.Series:
        """Chaikin A/D Oscillator"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        volume = self.df['volume'].values
        res = talib.ADOSC(high, low, close, volume, fastperiod=fastperiod, slowperiod=slowperiod)
        return pd.Series(res, index=self.df.index, name='ADOSC')

    def obv(self) -> pd.Series:
        """On Balance Volume"""
        close = self.df['close'].values
        volume = self.df['volume'].values
        res = talib.OBV(close, volume)
        return pd.Series(res, index=self.df.index, name='OBV')

    # CYCLE INDICATORS

    def ht_dcperiod(self) -> pd.Series:
        """Hilbert Transform - Dominant Cycle Period"""
        close = self.df['close'].values
        res = talib.HT_DCPERIOD(close)
        return pd.Series(res, index=self.df.index, name='HT_DCPERIOD')

    def ht_dcphase(self) -> pd.Series:
        """Hilbert Transform - Dominant Cycle Phase"""
        close = self.df['close'].values
        res = talib.HT_DCPHASE(close)
        return pd.Series(res, index=self.df.index, name='HT_DCPHASE')

    def ht_phasor(self) -> pd.DataFrame:
        """Hilbert Transform - Phasor Components"""
        close = self.df['close'].values
        inphase, quadrature = talib.HT_PHASOR(close)
        return pd.DataFrame({'inphase': inphase, 'quadrature': quadrature}, index=self.df.index)

    def ht_sine(self) -> pd.DataFrame:
        """Hilbert Transform - SineWave"""
        close = self.df['close'].values
        sine, leadsine = talib.HT_SINE(close)
        return pd.DataFrame({'sine': sine, 'leadsine': leadsine}, index=self.df.index)

    def ht_trendmode(self) -> pd.Series:
        """Hilbert Transform - Trend vs Cycle Mode"""
        close = self.df['close'].values
        res = talib.HT_TRENDMODE(close)
        return pd.Series(res, index=self.df.index, name='HT_TRENDMODE')

    # PRICE TRANSFORM

    def avgprice(self) -> pd.Series:
        """Average Price"""
        open_ = self.df['open'].values
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.AVGPRICE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='AVGPRICE')

    def medprice(self) -> pd.Series:
        """Median Price"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.MEDPRICE(high, low)
        return pd.Series(res, index=self.df.index, name='MEDPRICE')

    def typprice(self) -> pd.Series:
        """Typical Price"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.TYPPRICE(high, low, close)
        return pd.Series(res, index=self.df.index, name='TYPPRICE')

    def wclprice(self) -> pd.Series:
        """Weighted Close Price"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.WCLPRICE(high, low, close)
        return pd.Series(res, index=self.df.index, name='WCLPRICE')

    # VOLATILITY INDICATORS

    def atr(self, timeperiod=14) -> pd.Series:
        """Average True Range"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.ATR(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='ATR')

    def natr(self, timeperiod=14) -> pd.Series:
        """Normalized Average True Range"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.NATR(high, low, close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='NATR')

    def trange(self) -> pd.Series:
        """True Range"""
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        res = talib.TRANGE(high, low, close)
        return pd.Series(res, index=self.df.index, name='TRANGE')

    # STATISTIC FUNCTIONS

    def beta(self, timeperiod=5) -> pd.Series:
        """Beta"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.BETA(high, low, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='BETA')

    def correl(self, timeperiod=30) -> pd.Series:
        """Pearson's Correlation Coefficient (r)"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.CORREL(high, low, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='CORREL')

    def linearreg(self, timeperiod=14) -> pd.Series:
        """Linear Regression"""
        close = self.df['close'].values
        res = talib.LINEARREG(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='LINEARREG')

    def linearreg_angle(self, timeperiod=14) -> pd.Series:
        """Linear Regression Angle"""
        close = self.df['close'].values
        res = talib.LINEARREG_ANGLE(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='LINEARREG_ANGLE')

    def linearreg_intercept(self, timeperiod=14) -> pd.Series:
        """Linear Regression Intercept"""
        close = self.df['close'].values
        res = talib.LINEARREG_INTERCEPT(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='LINEARREG_INTERCEPT')

    def linearreg_slope(self, timeperiod=14) -> pd.Series:
        """Linear Regression Slope"""
        close = self.df['close'].values
        res = talib.LINEARREG_SLOPE(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='LINEARREG_SLOPE')

    def stddev(self, timeperiod=5, nbdev=1) -> pd.Series:
        """Standard Deviation"""
        close = self.df['close'].values
        res = talib.STDDEV(close, timeperiod=timeperiod, nbdev=nbdev)
        return pd.Series(res, index=self.df.index, name='STDDEV')

    def tsf(self, timeperiod=14) -> pd.Series:
        """Time Series Forecast"""
        close = self.df['close'].values
        res = talib.TSF(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='TSF')

    def var(self, timeperiod=5, nbdev=1) -> pd.Series:
        """Variance"""
        close = self.df['close'].values
        res = talib.VAR(close, timeperiod=timeperiod, nbdev=nbdev)
        return pd.Series(res, index=self.df.index, name='VAR')

    # MATH TRANSFORM

    def acos(self) -> pd.Series:
        """Vector Trigonometric ACos"""
        close = self.df['close'].values
        res = talib.ACOS(close)
        return pd.Series(res, index=self.df.index, name='ACOS')

    def asin(self) -> pd.Series:
        """Vector Trigonometric ASin"""
        close = self.df['close'].values
        res = talib.ASIN(close)
        return pd.Series(res, index=self.df.index, name='ASIN')

    def atan(self) -> pd.Series:
        """Vector Trigonometric ATan"""
        close = self.df['close'].values
        res = talib.ATAN(close)
        return pd.Series(res, index=self.df.index, name='ATAN')

    def ceil(self) -> pd.Series:
        """Vector Ceil"""
        close = self.df['close'].values
        res = talib.CEIL(close)
        return pd.Series(res, index=self.df.index, name='CEIL')

    def cos(self) -> pd.Series:
        """Vector Trigonometric Cos"""
        close = self.df['close'].values
        res = talib.COS(close)
        return pd.Series(res, index=self.df.index, name='COS')

    def cosh(self) -> pd.Series:
        """Vector Trigonometric Cosh"""
        close = self.df['close'].values
        res = talib.COSH(close)
        return pd.Series(res, index=self.df.index, name='COSH')

    def exp(self) -> pd.Series:
        """Vector Arithmetic Exp"""
        close = self.df['close'].values
        res = talib.EXP(close)
        return pd.Series(res, index=self.df.index, name='EXP')

    def floor(self) -> pd.Series:
        """Vector Floor"""
        close = self.df['close'].values
        res = talib.FLOOR(close)
        return pd.Series(res, index=self.df.index, name='FLOOR')

    def ln(self) -> pd.Series:
        """Vector Log Natural"""
        close = self.df['close'].values
        res = talib.LN(close)
        return pd.Series(res, index=self.df.index, name='LN')

    def log10(self) -> pd.Series:
        """Vector Log10"""
        close = self.df['close'].values
        res = talib.LOG10(close)
        return pd.Series(res, index=self.df.index, name='LOG10')

    def sin(self) -> pd.Series:
        """Vector Trigonometric Sin"""
        close = self.df['close'].values
        res = talib.SIN(close)
        return pd.Series(res, index=self.df.index, name='SIN')

    def sinh(self) -> pd.Series:
        """Vector Trigonometric Sinh"""
        close = self.df['close'].values
        res = talib.SINH(close)
        return pd.Series(res, index=self.df.index, name='SINH')

    def sqrt(self) -> pd.Series:
        """Vector Square Root"""
        close = self.df['close'].values
        res = talib.SQRT(close)
        return pd.Series(res, index=self.df.index, name='SQRT')

    def tan(self) -> pd.Series:
        """Vector Trigonometric Tan"""
        close = self.df['close'].values
        res = talib.TAN(close)
        return pd.Series(res, index=self.df.index, name='TAN')

    def tanh(self) -> pd.Series:
        """Vector Trigonometric Tanh"""
        close = self.df['close'].values
        res = talib.TANH(close)
        return pd.Series(res, index=self.df.index, name='TANH')

    # MATH OPERATORS

    def add(self) -> pd.Series:
        """Vector Arithmetic Add"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.ADD(high, low)
        return pd.Series(res, index=self.df.index, name='ADD')

    def div(self) -> pd.Series:
        """Vector Arithmetic Div"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.DIV(high, low)
        return pd.Series(res, index=self.df.index, name='DIV')

    def max(self, timeperiod=30) -> pd.Series:
        """Highest value over a specified period"""
        close = self.df['close'].values
        res = talib.MAX(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MAX')

    def maxindex(self, timeperiod=30) -> pd.Series:
        """Index of highest value over a specified period"""
        close = self.df['close'].values
        res = talib.MAXINDEX(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MAXINDEX')

    def min(self, timeperiod=30) -> pd.Series:
        """Lowest value over a specified period"""
        close = self.df['close'].values
        res = talib.MIN(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MIN')

    def minindex(self, timeperiod=30) -> pd.Series:
        """Index of lowest value over a specified period"""
        close = self.df['close'].values
        res = talib.MININDEX(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='MININDEX')

    def minmax(self, timeperiod=30) -> pd.DataFrame:
        """Lowest and highest values over a specified period"""
        close = self.df['close'].values
        min_val, max_val = talib.MINMAX(close, timeperiod=timeperiod)
        return pd.DataFrame({'min': min_val, 'max': max_val}, index=self.df.index)

    def minmaxindex(self, timeperiod=30) -> pd.DataFrame:
        """Indexes of lowest and highest values over a specified period"""
        close = self.df['close'].values
        minidx, maxidx = talib.MINMAXINDEX(close, timeperiod=timeperiod)
        return pd.DataFrame({'minidx': minidx, 'maxidx': maxidx}, index=self.df.index)

    def mult(self) -> pd.Series:
        """Vector Arithmetic Mult"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.MULT(high, low)
        return pd.Series(res, index=self.df.index, name='MULT')

    def sub(self) -> pd.Series:
        """Vector Arithmetic Substraction"""
        high = self.df['high'].values
        low = self.df['low'].values
        res = talib.SUB(high, low)
        return pd.Series(res, index=self.df.index, name='SUB')

    def sum(self, timeperiod=30) -> pd.Series:
        """Summation"""
        close = self.df['close'].values
        res = talib.SUM(close, timeperiod=timeperiod)
        return pd.Series(res, index=self.df.index, name='SUM')

    # PATTERN RECOGNITION

    def cdl2crows(self) -> pd.Series:
        """Two Crows"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL2CROWS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL2CROWS')

    def cdl3blackcrows(self) -> pd.Series:
        """Three Black Crows"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL3BLACKCROWS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL3BLACKCROWS')

    def cdl3inside(self) -> pd.Series:
        """Three Inside Up/Down"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL3INSIDE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL3INSIDE')

    def cdl3linestrike(self) -> pd.Series:
        """Three-Line Strike"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL3LINESTRIKE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL3LINESTRIKE')

    def cdl3outside(self) -> pd.Series:
        """Three Outside Up/Down"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL3OUTSIDE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL3OUTSIDE')

    def cdl3starsinsouth(self) -> pd.Series:
        """Three Stars In The South"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL3STARSINSOUTH(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL3STARSINSOUTH')

    def cdl3whitesoldiers(self) -> pd.Series:
        """Three Advancing White Soldiers"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDL3WHITESOLDIERS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDL3WHITESOLDIERS')

    def cdlabandonedbaby(self, penetration=0.3) -> pd.Series:
        """Abandoned Baby"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLABANDONEDBABY(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLABANDONEDBABY')

    def cdladvanceblock(self) -> pd.Series:
        """Advance Block"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLADVANCEBLOCK(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLADVANCEBLOCK')

    def cdlbelthold(self) -> pd.Series:
        """Belt-hold"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLBELTHOLD(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLBELTHOLD')

    def cdlbreakaway(self) -> pd.Series:
        """Breakaway"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLBREAKAWAY(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLBREAKAWAY')

    def cdlclosingmarubozu(self) -> pd.Series:
        """Closing Marubozu"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLCLOSINGMARUBOZU(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLCLOSINGMARUBOZU')

    def cdlconcealbabyswall(self) -> pd.Series:
        """Concealing Baby Swallow"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLCONCEALBABYSWALL(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLCONCEALBABYSWALL')

    def cdlcounterattack(self) -> pd.Series:
        """Counterattack"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLCOUNTERATTACK(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLCOUNTERATTACK')

    def cdldarkcloudcover(self, penetration=0.5) -> pd.Series:
        """Dark Cloud Cover"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLDARKCLOUDCOVER(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLDARKCLOUDCOVER')

    def cdldoji(self) -> pd.Series:
        """Doji"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLDOJI(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLDOJI')

    def cdldojistar(self) -> pd.Series:
        """Doji Star"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLDOJISTAR(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLDOJISTAR')

    def cdldragonflydoji(self) -> pd.Series:
        """Dragonfly Doji"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLDRAGONFLYDOJI(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLDRAGONFLYDOJI')

    def cdlengulfing(self) -> pd.Series:
        """Engulfing Pattern"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLENGULFING(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLENGULFING')

    def cdleveningdojistar(self, penetration=0.3) -> pd.Series:
        """Evening Doji Star"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLEVENINGDOJISTAR(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLEVENINGDOJISTAR')

    def cdleveningstar(self, penetration=0.3) -> pd.Series:
        """Evening Star"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLEVENINGSTAR(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLEVENINGSTAR')

    def cdlgapsidesidewhite(self) -> pd.Series:
        """Up/Down-gap side-by-side white lines"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLGAPSIDESIDEWHITE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLGAPSIDESIDEWHITE')

    def cdlgravestonedoji(self) -> pd.Series:
        """Gravestone Doji"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLGRAVESTONEDOJI(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLGRAVESTONEDOJI')

    def cdlhammer(self) -> pd.Series:
        """Hammer"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHAMMER(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHAMMER')

    def cdlhangingman(self) -> pd.Series:
        """Hanging Man"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHANGINGMAN(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHANGINGMAN')

    def cdlharami(self) -> pd.Series:
        """Harami Pattern"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHARAMI(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHARAMI')

    def cdlharamicross(self) -> pd.Series:
        """Harami Cross Pattern"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHARAMICROSS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHARAMICROSS')

    def cdlhighwave(self) -> pd.Series:
        """High-Wave Candle"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHIGHWAVE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHIGHWAVE')

    def cdlhikkake(self) -> pd.Series:
        """Hikkake Pattern"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHIKKAKE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHIKKAKE')

    def cdlhikkakemod(self) -> pd.Series:
        """Modified Hikkake Pattern"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHIKKAKEMOD(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHIKKAKEMOD')

    def cdlhomingpigeon(self) -> pd.Series:
        """Homing Pigeon"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLHOMINGPIGEON(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLHOMINGPIGEON')

    def cdlidentical3crows(self) -> pd.Series:
        """Identical Three Crows"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLIDENTICAL3CROWS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLIDENTICAL3CROWS')

    def cdlinneck(self) -> pd.Series:
        """In-Neck Pattern"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLINNECK(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLINNECK')

    def cdlinvertedhammer(self) -> pd.Series:
        """Inverted Hammer"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLINVERTEDHAMMER(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLINVERTEDHAMMER')

    def cdlkicking(self) -> pd.Series:
        """Kicking"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLKICKING(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLKICKING')

    def cdlkickingbylength(self) -> pd.Series:
        """Kicking - bull/bear determined by the longer marubozu"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLKICKINGBYLENGTH(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLKICKINGBYLENGTH')

    def cdlladderbottom(self) -> pd.Series:
        """Ladder Bottom"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLLADDERBOTTOM(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLLADDERBOTTOM')

    def cdllongleggeddoji(self) -> pd.Series:
        """Long Legged Doji"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLLONGLEGGEDDOJI(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLLONGLEGGEDDOJI')

    def cdllongline(self) -> pd.Series:
        """Long Line Candle"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLLONGLINE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLLONGLINE')

    def cdlmarubozu(self) -> pd.Series:
        """Marubozu"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLMARUBOZU(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLMARUBOZU')

    def cdlmatchinglow(self) -> pd.Series:
        """Matching Low"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLMATCHINGLOW(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLMATCHINGLOW')

    def cdlmathold(self, penetration=0.5) -> pd.Series:
        """Mat Hold"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLMATHOLD(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLMATHOLD')

    def cdlmorningdojistar(self, penetration=0.3) -> pd.Series:
        """Morning Doji Star"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLMORNINGDOJISTAR(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLMORNINGDOJISTAR')

    def cdlmorningstar(self, penetration=0.3) -> pd.Series:
        """Morning Star"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLMORNINGSTAR(open_, high, low, close, penetration=penetration)
        return pd.Series(res, index=self.df.index, name='CDLMORNINGSTAR')

    def cdlonneck(self) -> pd.Series:
        """On-Neck Pattern"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLONNECK(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLONNECK')

    def cdlpiercing(self) -> pd.Series:
        """Piercing Pattern"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLPIERCING(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLPIERCING')

    def cdlrickshawman(self) -> pd.Series:
        """Rickshaw Man"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLRICKSHAWMAN(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLRICKSHAWMAN')

    def cdlrisefall3methods(self) -> pd.Series:
        """Rising/Falling Three Methods"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLRISEFALL3METHODS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLRISEFALL3METHODS')

    def cdlseparatinglines(self) -> pd.Series:
        """Separating Lines"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLSEPARATINGLINES(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLSEPARATINGLINES')

    def cdlshootingstar(self) -> pd.Series:
        """Shooting Star"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLSHOOTINGSTAR(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLSHOOTINGSTAR')

    def cdlshortline(self) -> pd.Series:
        """Short Line Candle"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLSHORTLINE(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLSHORTLINE')

    def cdlspinningtop(self) -> pd.Series:
        """Spinning Top"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLSPINNINGTOP(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLSPINNINGTOP')

    def cdlstalledpattern(self) -> pd.Series:
        """Stalled Pattern"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLSTALLEDPATTERN(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLSTALLEDPATTERN')

    def cdlsticksandwich(self) -> pd.Series:
        """Stick Sandwich"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLSTICKSANDWICH(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLSTICKSANDWICH')

    def cdltakuri(self) -> pd.Series:
        """Takuri (Dragonfly Doji with very long lower shadow)"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLTAKURI(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLTAKURI')

    def cdltasukigap(self) -> pd.Series:
        """Tasuki Gap"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLTASUKIGAP(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLTASUKIGAP')

    def cdlthrusting(self) -> pd.Series:
        """Thrusting Pattern"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLTHRUSTING(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLTHRUSTING')

    def cdltristar(self) -> pd.Series:
        """Tristar Pattern"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLTRISTAR(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLTRISTAR')

    def cdlunique3river(self) -> pd.Series:
        """Unique 3 River"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLUNIQUE3RIVER(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLUNIQUE3RIVER')

    def cdlupsidegap2crows(self) -> pd.Series:
        """Upside Gap Two Crows"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLUPSIDEGAP2CROWS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLUPSIDEGAP2CROWS')

    def cdlxsidegap3methods(self) -> pd.Series:
        """Upside/Downside Gap Three Methods"""
        open_, high, low, close = self.df['open'].values, self.df['high'].values, self.df['low'].values, self.df['close'].values
        res = talib.CDLXSIDEGAP3METHODS(open_, high, low, close)
        return pd.Series(res, index=self.df.index, name='CDLXSIDEGAP3METHODS')

