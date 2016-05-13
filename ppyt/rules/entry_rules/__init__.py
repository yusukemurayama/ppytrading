# coding: utf-8
import logging
import abc
from ppyt import const
from ppyt.rules import RuleBase
from ppyt.decorators import handle_nodataerror
from ppyt.exceptions import OrderTypeError

logger = logging.getLogger(__name__)


class EntryBase(RuleBase, metaclass=abc.ABCMeta):
    """entry_ruleの親クラスです。"""

    _rule_type = const.RULE_TYPE_ENTRYRULES

    def __init__(self, timing=const.ORDER_TIMING_ANYTIME, *args, **kwds):
        """コンストラクタ

        Args:
            timing: 注文するタイミング（寄付 or ザラ場中 or 引け or いつでも）
        """
        self.timing = timing
        super().__init__(*args, **kwds)
        self._setup(*args, **kwds)

    @abc.abstractmethod
    def _get_entry_price_long(self, idx, timing):
        """買い仕掛けの価格を取得します。仕掛ける条件を満たしていない場合はNoneが返ります。"""
        pass

    @abc.abstractmethod
    def _get_entry_price_short(self, idx, timing):
        """売り仕掛けの価格を取得します。仕掛ける条件を満たしていない場合はNoneが返ります。"""
        pass

    @handle_nodataerror(None)
    def get_entry_price(self, order_type, idx, timing, check_pricerange=True):
        """仕掛け価格を取得します。仕掛ける条件を満たしていない場合はNoneが返ります。

        Args:
            order_type: 購入種別
            idx: 日付を特定するindex
            timing: 注文タイミング
            check_pricerange: 仕掛け価格が安値・高値の間に入っているかをチェックします。
                              ※backtestでは常にTrueにします。

        Returns:
            注文価格
        """
        entry_price = None
        if order_type == const.ORDER_TYPE_LONG:
            entry_price = self._get_entry_price_long(idx, timing)
        elif order_type == const.ORDER_TYPE_SHORT:
            entry_price = self._get_entry_price_short(idx, timing)
        else:
            raise OrderTypeError(order_type)

        if entry_price is not None and check_pricerange:
            # 安値と高値の範囲に入っていない場合は仕掛けないようにします。
            if entry_price < self.get_low_price(idx) or entry_price > self.get_high_price(idx):
                entry_price = None

        if entry_price is not None:
            entry_price = float(entry_price)

        return entry_price

    def is_timing_matched(self, timing):
        """引数で指定された注文タイミングと、クラスに設定されている注文タイミングの一致を判定します。

        Args:
            timing: 注文タイミング
        """
        if self.timing == const.ORDER_TIMING_ANYTIME:
            return True  # ANYTIMEの場合は必ずTrueになります。
        return self.timing == timing  # タイミング指定がある場合は一致しているかを見ます。


class EntryTemplate(EntryBase):
    """entry_ruleのテンプレートです。"""

    _findkey = 'テンプレート'  # entry_ruleを一意に特定できる名前をつけます。

    def _setup(self):
        """初期化時に呼ばれます。パラメータ類を設定します。"""
        pass

    def _update(self):
        """銘柄を入れ替えたタイミングで呼ばれます。インスタンス変数を更新します。"""
        pass

    def _get_entry_price_long(self, idx, timing):
        """買い仕掛け時の金額を取得します。

        Args:
            idx: 日付を特定するindex
            timing: 注文タイミング

        Returns:
            買い仕掛けの価格（仕掛けできない場合はNoneを返す）
        """
        return None

    def _get_entry_price_short(self, idx, timing):
        """売り仕掛け時の金額を取得します。

        Args:
            idx: 日付を特定するindex
            timing: 注文タイミング

        Returns:
            売り仕掛けの価格（仕掛けできない場合はNoneを返す）
        """
        return None
