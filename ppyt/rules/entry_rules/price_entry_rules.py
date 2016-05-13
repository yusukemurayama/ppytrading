# coding: utf-8
import logging
from ppyt import const
from ppyt.rules.entry_rules import EntryBase
from ppyt.indicators.basic_indicators import (
    RecentHighPriceIndicator, RecentLowPriceIndicator,
)

logger = logging.getLogger(__name__)


class BreakoutEntry(EntryBase):
    """価格のブレイクアウトを見て仕掛けるクラスです。"""

    _findkey = 'ブレイクアウト'  # entry_ruleを一意に特定できる名前をつけます。

    def _setup(self, span=None, percentage=None):
        """初期化します。

        Args:
            span: 過去何日間の高値・安値を見るかを決定します。
            percentage: 仕掛け価格を決定します。
                高値・安値と同時に仕掛ける場合は0を指定します。

        Raises:
            ArgumentError: 引数チェックに引っかかった場合に発生します。
        """
        self._is_valid_argument('span', span, int)
        self._is_valid_argument('percentage', percentage, int, float)

        self.span = span
        self.rate_long = 1 + percentage * 0.01
        self.rate_short = 1 - percentage * 0.01

    def _update(self):
        """銘柄更新時に呼ばれます。銘柄変更に伴い、indicatorを生成しなおします。"""
        self.recent_high_indicator = RecentHighPriceIndicator(stock=self.stock, span=self.span)
        self.recent_low_indicator = RecentLowPriceIndicator(stock=self.stock, span=self.span)

    def _get_entry_price_long(self, idx, timing):
        """買い仕掛け時の金額を取得します。

        仕掛け:
            - 昨日の高値が過去N日間の高値よりも低く、本日の始値が過去N日間の高値を超える
            - 仕掛ける価格は「過去N日間の高値 * (1 + percentage * 0.01)」

        Args:
            idx: 日付を特定するindex
            timing: 注文タイミング

        Returns:
            買い仕掛けの価格（仕掛けできない場合はNoneを返す）
        """
        entry_price = None
        recent_high = self.recent_high_indicator.get(idx-1)  # 昨日時点の直近高値
        # 昨日の価格が直近高値未満で、本日の始値が直近高値を超えた場合
        if timing == const.ORDER_TIMING_SESSION:  # ザラ場中に仕掛けます。
            if self.get_high_price(idx-1) < recent_high and self.get_open_price(idx) > recent_high:
                # 仕掛け価格を取得します。
                entry_price = recent_high * self.rate_long

        return entry_price

    def _get_entry_price_short(self, idx, timing):
        """売り仕掛け時の金額を取得します。

        仕掛け:
            - 昨日の安値が過去N日間の安値よりも高く、本日の始値が過去N日間の安値を下回る
            - 仕掛ける価格は「過去N日間の安値 * (1 - percentage * 0.01)」

        Args:
            idx: 日付を特定するindex
            timing: 注文タイミング

        Returns:
            売り仕掛けの価格（仕掛けできない場合はNoneを返す）
        """
        entry_price = None
        recent_low = self.recent_low_indicator.get(idx-1)  # 昨日時点の直近安値
        # 昨日の価格が直近安値未満で、本日の始値が直近安値を超えた場合
        if timing == const.ORDER_TIMING_SESSION:  # ザラ場中に仕掛けます。
            if self.get_low_price(idx-1) > recent_low and self.get_open_price(idx) < recent_low:
                # 仕掛け価格を取得します。
                entry_price = recent_low * self.rate_short

        return entry_price
