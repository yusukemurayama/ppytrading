# coding: utf-8
import logging
from ppyt import const
from ppyt.indicators import IndicatorBase
from ppyt.indicators.basic_indicators import (
    PriceIndicator, RecentHighPriceIndicator, RecentLowPriceIndicator
)

logger = logging.getLogger(__name__)


class CloseGtRecentHighIndicator(IndicatorBase):
    """終値が直近高値より上かを表す指標です。"""
    _findkey = 'CloseGtRecentHigh'

    def _build_indicator(self, span, **kwds):
        """indicatorのデータを組み立てます。

        Args:
            span: 過去何日間の高値を上に抜いたか
        """
        recent_indicator = RecentHighPriceIndicator(stock=self.stock,
                                                    span=span)
        price_indicator = PriceIndicator(stock=self.stock,
                                         price_type=const.PRICE_TYPE_CLOSE)

        arr1 = recent_indicator.shifted(-1)  # 昨日
        arr2 = price_indicator.data  # 当日

        # 昨日の終値が一昨日のX日間高値を上回っているかを判定します。
        return arr1 < arr2


class CloseLtRecentLowIndicator(IndicatorBase):
    """終値が直近安値より下かを表す指標です。"""
    _findkey = 'CloseLtRecentLow'

    def _build_indicator(self, span, **kwds):
        """indicatorのデータを組み立てます。

        Args:
            span: 過去何日間の高値を上に抜いたか
        """
        recent_indicator = RecentLowPriceIndicator(stock=self.stock,
                                                   span=span)
        price_indicator = PriceIndicator(stock=self.stock,
                                         price_type=const.PRICE_TYPE_CLOSE)

        arr1 = recent_indicator.shifted(-1)  # 昨日
        arr2 = price_indicator.data  # 当日

        # 昨日の終値が一昨日のX日間安値を下回っているかを判定します。
        return arr1 > arr2
