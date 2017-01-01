# coding: utf-8
import logging
import numpy as np
from ppyt.indicators import IndicatorBase
from ppyt.indicators.basic_indicators import MovingAverageIndicator
from ppyt import const

logger = logging.getLogger(__name__)


class MADirectionIndicator(IndicatorBase):
    """移動平均線の向きを表す指標です。"""
    _findkey = '移動平均線の向き'

    def _build_indicator(self, span, **kwds):
        """indicatorのデータを組み立てます。

        Args:
            span: 移動平均線の集計日数
        """
        def get_direction(val1, val2):
            if np.isnan(val1) or np.isnan(val1):
                return np.nan
            elif val1 < val2:
                return const.INDI_DIRECTION_UP  # 上向き
            elif val1 > val2:
                return const.INDI_DIRECTION_DOWN  # 下向き
            else:
                return const.INDI_DIRECTION_HR  # 水平

        ma = MovingAverageIndicator(stock=self.stock, span=span)
        arr1 = ma.shifted(-1)  # 一つ前
        arr2 = ma.data  # 最新
        return np.array([get_direction(a, b) for a, b
                         in zip(arr1, arr2)], dtype=np.float16)
