# coding: utf-8
import logging
from ppyt import const
from ppyt.rules.entry_rules import EntryBase

logger = logging.getLogger(__name__)


class SimpleEntry(EntryBase):
    """（conditionsを覗いて）条件なしで仕掛けるクラスです。"""

    _findkey = '条件なし'  # entry_ruleを一意に特定できる名前をつけます。

    def _setup(self):
        """初期化時に呼ばれます。パラメータ類を設定します。

        Raises:
            ArgumentError: 引数チェックに引っかかった場合に発生します。
        """
        pass

    def _update(self):
        """銘柄を入れ替えたタイミングで呼ばれます。インスタンス変数を更新します。"""
        pass

    def _get_entry_price_long(self, idx, timing):
        """買い仕掛け時の金額を取得します。
        特に条件はなく、注文タイミングにしたがって価格を返します。
        ザラ場中に関しては、価格を決める要因がないので、注文自体をできないようにします。

        Args:
            idx: 日付を特定するindex
            timing: 注文タイミング

        Returns:
            買い仕掛けの価格（仕掛けできない場合はNoneを返す）
        """
        if timing == const.ORDER_TIMING_OPEN:
            return self.get_open_price(idx)
        elif timing == const.ORDER_TIMING_SESSION:
            return None
        elif timing == const.ORDER_TIMING_CLOSE:
            return self.get_close_price(idx)

    def _get_entry_price_short(self, idx, timing):
        """売り仕掛け時の金額を取得します。
        特に条件はなく、注文タイミングにしたがって価格を返します。
        ザラ場中に関しては、価格を決める要因がないので、注文自体をできないようにします。

        Args:
            idx: 日付を特定するindex
            timing: 注文タイミング

        Returns:
            売り仕掛けの価格（仕掛けできない場合はNoneを返す）
        """
        if timing == const.ORDER_TIMING_OPEN:
            return self.get_open_price(idx)
        elif timing == const.ORDER_TIMING_SESSION:
            return None
        elif timing == const.ORDER_TIMING_CLOSE:
            return self.get_close_price(idx)
