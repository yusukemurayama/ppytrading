# coding: utf-8
import logging
from ppyt.rules.conditions import ConditionBase
from ppyt.indicators.breakout_indicators import (
    UpperBreakoutIndicator, LowerBreakoutIndicator
)

logger = logging.getLogger(__name__)


class BreakoutCondition(ConditionBase):
    """ブレイクアウトしたかを判定します。"""
    _findkey = 'Breakout'

    def _setup(self, span):
        """コンストラクタ

        Args:
            span: 過去何日間の高値・安値を抜けたか

        Raises:
            ArgumentError: 引数チェックに引っかかった場合に発生します。
        """
        self.span = span

    def _update(self):
        """インスタンス変数を更新します。"""
        self.u_bo_indicator = UpperBreakoutIndicator(
            stock=self.stock, span=self.span)
        self.l_bo_indicator = LowerBreakoutIndicator(
            stock=self.stock, span=self.span)

    def _can_entry_long(self, idx):
        # 前日の高値が、一昨日までのX日間高値を超えているかを判定します。
        return self.u_bo_indicator.data[idx - 1]

    def _can_entry_short(self, idx):
        # 前日の安値が、一昨日までのX日間安値を超えているかを判定します。
        return self.l_bo_indicator.data[idx - 1]

    def _can_exit_long(self, idx):
        # Exitはチェックせずに全て通します。
        return True

    def _can_exit_short(self, idx):
        # Exitはチェックせずに全て通します。
        return True
