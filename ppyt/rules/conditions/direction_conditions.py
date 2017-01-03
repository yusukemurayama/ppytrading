# coding: utf-8
import logging
from ppyt import const
from ppyt.rules.conditions import ConditionBase
from ppyt.indicators.direction_indicators import MADirectionIndicator

logger = logging.getLogger(__name__)


class MADirectionCondition(ConditionBase):
    """移動平均線の向きを判定するクラスです。"""
    _findkey = 'MA Direction'

    def _setup(self, span_short=None, span=None):
        """コンストラクタ

        Args:
            span: 移動平均線の期間　

        Raises:
            ArgumentError: 引数チェックに引っかかった場合に発生します。
        """
        self._is_valid_argument('span', span, int)

        self.span = span

    def _update(self):
        """インスタンス変数を更新します。"""
        self.ma_direction = MADirectionIndicator(stock=self.stock,
                                                 span=self.span)

    def _can_entry_long(self, idx):
        """買い仕掛けができるかを判定します。"""
        # 移動平均線が上向きかを判定します。
        return self.ma_direction.get(idx - 1) == const.INDI_DIRECTION_UP

    def _can_entry_short(self, idx):
        """売り仕掛けができるかを判定します。"""
        # 移動平均線が下向きかを判定します。
        return self.ma_direction.get(idx - 1) == const.INDI_DIRECTION_DOWN
