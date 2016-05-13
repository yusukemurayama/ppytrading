# coding: utf-8
from ppyt.indicators import IndicatorBase
from ppyt.indicators.basic_indicators import MovingAverageIndicator
import numpy as np


class CrossOverIndicator(IndicatorBase):
    """クロスオーバーが発生したことを表すindicatorです。"""

    _findkey = '移動平均線のクロス'  # indicatorを一意に特定できる名前をつけます。

    def _build_indicator(self, span_short, span_long, reverse=False):
        """indicatorのデータを組み立てます。

        Args:
            span_short: 短期の移動平均線の集計日数
            span_long: 長期の移動平均線の集計日数
            reverse: Falseにすると短期が長期を上に抜けるタイミングを調べる。
                     Trueにすると短期が長期を下に抜けるタイミングを調べる。
        Returns:
            indicatorのデータ（numpyの配列）
        """
        ma_short = MovingAverageIndicator(stock=self.stock, span=span_short)
        ma_long = MovingAverageIndicator(stock=self.stock, span=span_long)

        if not reverse:  # 上に抜ける。
            arr1 = ma_short.shifted(-2) < ma_long.shifted(-2)  # 一昨日を比較
            arr2 = ma_short.shifted(-1) >= ma_long.shifted(-1)  # 昨日を比較
            return np.logical_and(arr1, arr2)

        else:  # 下に抜ける。
            arr1 = ma_short.shifted(-2) > ma_long.shifted(-2)  # 一昨日を比較
            arr2 = ma_short.shifted(-1) <= ma_long.shifted(-1)  # 昨日を比較
            return np.logical_and(arr1, arr2)
