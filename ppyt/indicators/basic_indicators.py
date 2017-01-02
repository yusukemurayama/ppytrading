# coding: utf-8
import numpy as np
from ppyt import const
from ppyt.indicators import IndicatorBase


class PriceIndicator(IndicatorBase):
    """価格のindicatorです。"""

    _findkey = '価格'  # indicatorを一意に特定できる名前をつけます。

    def _build_indicator(self, price_type=const.PRICE_TYPE_CLOSE, **kwds):
        """indicatorのデータを組み立てます。

        Args:
            price_type: 価格の種別

        Returns:
            indicatorのデータ（numpyの配列）
        """
        return np.array(self.stock.get_prices(price_type), dtype=np.float64)


class MovingAverageIndicator(IndicatorBase):
    """移動平均線のindicatorです。"""

    _findkey = '移動平均線'  # indicatorを一意に特定できる名前をつけます。

    def _build_indicator(self, price_type=const.PRICE_TYPE_CLOSE, **kwds):
        """indicatorのデータを組み立てます。

        Args:
            price_type: 価格の種別

        Returns:
            indicatorのデータ（numpyの配列）
        """
        return np.average(self.spanned_data(price_type), axis=1)


class RecentHighPriceIndicator(IndicatorBase):
    """直近高値のindicatorです。"""

    _findkey = '直近高値'  # indicatorを一意に特定できる名前をつけます。

    def _build_indicator(self, price_type=const.PRICE_TYPE_HIGH, **kwds):
        """indicatorのデータを組み立てます。

        Args:
            price_type: 価格の種別

        Returns:
            indicatorのデータ（numpyの配列）
        """
        return np.max(self.spanned_data(price_type), axis=1)


class RecentLowPriceIndicator(IndicatorBase):
    _findkey = '直近安値'

    def _build_indicator(self, price_type=const.PRICE_TYPE_LOW, **kwds):
        """indicatorのデータを組み立てます。

        Args:
            price_type: 価格の種別

        Returns:
            indicatorのデータ（numpyの配列）
        """
        return np.min(self.spanned_data(price_type), axis=1)
