# coding: utf-8
import logging
import abc
from ppyt import const
from ppyt.rules import RuleBase
from ppyt.decorators import handle_nodataerror
from ppyt.exceptions import OrderTypeError

logger = logging.getLogger(__name__)


class ExitBase(RuleBase, metaclass=abc.ABCMeta):
    """exit_ruleの親クラスです。"""

    _rule_type = const.RULE_TYPE_EXITRULES

    def __init__(self, timing=const.ORDER_TIMING_ANYTIME, *args, **kwds):
        """コンストラクタ

        Args:
            timing: 注文するタイミング（寄付 or ザラ場中 or 引け or いつでも）
        """
        self.timing = timing
        super().__init__(*args, **kwds)
        self._setup(*args, **kwds)

    @abc.abstractmethod
    def _get_exit_price_long(self, position, idx, timing):
        """買いポジションに対する手仕舞い価格を取得します。
        手仕舞う条件を満たしていない場合はNoneが返ります。"""
        pass

    @abc.abstractmethod
    def _get_exit_price_short(self, position, idx, timing):
        """売りポジションに対する手仕舞い価格を取得します。
        手仕舞う条件を満たしていない場合はNoneが返ります。"""
        pass

    @handle_nodataerror(None)
    def get_exit_price(self, position, idx, timing, check_pricerange=True):
        """手仕舞い価格を取得します。手仕舞う条件を満たしていない場合はNoneが返ります。

        Args:
            position: 保有中のポジション情報
            idx: 日付を特定するindex
            timing: 注文タイミング
            check_pricerange: 仕掛け価格が安値・高値の間に入っているかをチェックします。
                              ※backtestでは常にTrueにします。

        Returns:
            手仕舞う価格
        """
        exit_price = None

        # 手仕舞う価格を取得します。
        if position.is_order_long:
            exit_price = self._get_exit_price_long(position=position, idx=idx, timing=timing)
        elif position.is_order_short:
            exit_price = self._get_exit_price_short(position=position, idx=idx, timing=timing)
        else:
            raise OrderTypeError(position.order_type)

        if exit_price is not None and check_pricerange:
            # 安値と高値の範囲に入っていない場合は強制的に手仕舞います。
            if exit_price < self.get_low_price(idx) or exit_price > self.get_high_price(idx):
                exit_price = self.get_high_price(idx) if position.is_order_long else self.get_low_price(idx)

        if exit_price is not None:
            exit_price = float(exit_price)

        return exit_price

    def is_timing_matched(self, timing):
        """引数で指定された注文タイミングと、クラスに設定されている注文タイミングの一致を判定します。

        Args:
            timing: 注文タイミング
        """
        if self.timing == const.ORDER_TIMING_ANYTIME:
            return True
        return self.timing == timing


class ExitTemplate(ExitBase):
    """exit_rule系クラスのテンプレートです。"""

    _findkey = 'テンプレート'  # exit_ruleを一意に特定できる名前をつけます。

    def _setup(self, period):
        """初期化時に呼ばれます。パラメータ類を設定します。"""
        pass

    def _update(self):
        """銘柄を入れ替えたタイミングで呼ばれます。インスタンス変数を更新します。"""
        pass

    def _get_exit_price_long(self, position, idx, timing):
        """買いポジションに対する手仕舞い価格を取得します。

        Args:
            position: 保有中のポジション情報
            idx: 日付を特定するindex
            timing: 注文タイミング

        Returns:
            手仕舞う価格（手仕舞わない場合はNoneを返す）
        """
        return None

    def _get_exit_price_short(self, position, idx, timing):
        """売りポジションに対する手仕舞い価格を取得します。

        Args:
            position: 保有中のポジション情報
            idx: 日付を特定するindex
            timing: 注文タイミング

        Returns:
            手仕舞う価格（手仕舞わない場合はNoneを返す）
        """
        return None
