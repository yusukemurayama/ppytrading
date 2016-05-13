# coding: utf-8
import logging
from ppyt.rules.conditions import ConditionBase
from ppyt.indicators.basic_indicators import MovingAverageIndicator
from ppyt.indicators.boolean_indicators import CrossOverIndicator

logger = logging.getLogger(__name__)


class MovingAverageCrossoverCondition(ConditionBase):
    """移動平均線がクロスオーバーしているかを判定するクラスです。"""

    _findkey = '移動平均線のクロスオーバー'  # conditionを一意に特定できる名前をつけます。

    def _setup(self, span_short=None, span_long=None):
        """コンストラクタ

        Args:
            span_short: 短期の集計期間
            span_long: 長期の集計期間

        Raises:
            ArgumentError: 引数チェックに引っかかった場合に発生します。
        """
        self._is_valid_argument('span_short', span_short, int)
        self._is_valid_argument('span_long', span_long, int)

        self.span_short = span_short
        self.span_long = span_long

    def _update(self):
        """インスタンス変数を更新します。"""
        self.ma_short = MovingAverageIndicator(stock=self.stock, span=self.span_short)
        self.ma_long = MovingAverageIndicator(stock=self.stock, span=self.span_long)

    def _can_entry_long(self, idx):
        """買い仕掛けができるかを判定します。

        Args:
            idx: 日付を特定するindex

        Returns:
            仕掛けができる場合はTrue、できない場合はFalse
        """
        ma_short1 = self.ma_short.get(idx-2)  # 短期の移動平均（一昨日）
        ma_short2 = self.ma_short.get(idx-1)  # 短期の移動平均（昨日）
        ma_long1 = self.ma_long.get(idx-2)  # 長期の移動平均（一昨日）
        ma_long2 = self.ma_long.get(idx-1)  # 長期の移動平均（昨日）

        if ma_short1 <= ma_long1 and ma_short2 > ma_long2:
            # 短期の移動平均線が長期の移動平均線を上に抜けた場合
            return True
        return False

    def _can_entry_short(self, idx):
        """売り仕掛けができるかを判定します。

        Args:
            idx: 日付を特定するindex

        Returns:
            仕掛けができる場合はTrue、できない場合はFalse
        """
        ma_short1 = self.ma_short.get(idx-2)  # 短期の移動平均（一昨日）
        ma_short2 = self.ma_short.get(idx-1)  # 短期の移動平均（昨日）
        ma_long1 = self.ma_long.get(idx-2)  # 長期の移動平均（一昨日）
        ma_long2 = self.ma_long.get(idx-1)  # 長期の移動平均（昨日）

        if ma_long1 <= ma_short1 and ma_long2 > ma_short2:
            # 短期の移動平均線が長期の移動平均線を下に抜けた場合
            return True
        return False


class MovingAverageCrossoverCondition2(ConditionBase):
    """移動平均線がクロスオーバーしているかを判定するクラスです。
    判定時にCrossOverIndicatorを使うようにしています。"""

    _findkey = '移動平均線のクロスオーバー2'  # conditionを一意に特定できる名前をつけます。

    def _setup(self, span_short=None, span_long=None):
        """コンストラクタ

        Args:
            span_short: 短期の集計期間
            span_long: 長期の集計期間

        Raises:
            ArgumentError: 引数チェックに引っかかった場合に発生します。
        """
        self._is_valid_argument('span_short', span_short, int)
        self._is_valid_argument('span_long', span_long, int)

        self.span_short = span_short
        self.span_long = span_long

    def _update(self):
        """インスタンス変数を更新します。"""
        # 短期移動平均線が長期移動平均線を上に抜けたかを保持するindicatorを生成します。
        self.array_long = CrossOverIndicator(stock=self.stock, span_short=self.span_short,
                                             span_long=self.span_long)

        # 短期移動平均線が長期移動平均線を下に抜けたかを保持するindicatorを生成します。
        self.array_short = CrossOverIndicator(stock=self.stock, span_short=self.span_short,
                                              span_long=self.span_long, reverse=True)

    def _can_entry_long(self, idx):
        """買い仕掛けができるかを判定します。

        Args:
            idx: 日付を特定するindex

        Returns:
            仕掛けができる場合はTrue、できない場合はFalse
        """
        return self.array_long.get(idx)

    def _can_entry_short(self, idx):
        """売り仕掛けができるかを判定します。

        Args:
            idx: 日付を特定するindex

        Returns:
            仕掛けができる場合はTrue、できない場合はFalse
        """
        return self.array_short.get(idx)
