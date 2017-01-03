# coding: utf-8
import logging
import numpy as np
from ppyt.indicators import IndicatorBase
from ppyt.indicators.closerecenthighlow_indicators import (
    CloseGtRecentHighIndicator, CloseLtRecentLowIndicator
)

logger = logging.getLogger(__name__)


class UpperBreakoutIndicator(IndicatorBase):
    """上にブレイクアウトしたかを示す指標です。"""
    _findkey = 'UpperBreakout'

    def _build_indicator(self, span, **kwds):
        """indicatorのデータを組み立てます。

        Args:
            span: 過去何日間の高値を上に抜いたか
        """
        # 当日の高値が、前日までの直近高値を超えたかの指標を取得します。
        indi = CloseGtRecentHighIndicator(stock=self.stock, span=span)
        arr1 = indi.data

        # 1日過去にずらした配列を取得します。
        arr2 = indi.shifted(-1)

        # 前日は直近高値以下で、当日に直近高値を超えているかを判定します。
        return np.logical_and(arr1, np.logical_not(arr2))


class LowerBreakoutIndicator(IndicatorBase):
    """下にブレイクアウトしたかを示す指標です。"""
    _findkey = 'LowerBreakout'

    def _build_indicator(self, span, **kwds):
        """indicatorのデータを組み立てます。

        Args:
            span: 過去何日間の高値を上に抜いたか
        """
        # 当日の安値が、前日までの直近安値を下回った指標を取得します。
        indi = CloseLtRecentLowIndicator(stock=self.stock, span=span)
        arr1 = indi.data

        # 1日過去にずらした配列を取得します。
        arr2 = indi.shifted(-1)

        # 前日は直近安値以上で、当日に直近安値未満かを判定します。
        return np.logical_and(arr1, np.logical_not(arr2))
