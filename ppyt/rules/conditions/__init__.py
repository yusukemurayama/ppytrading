# coding: utf-8
import logging
import abc
from ppyt import const
from ppyt.exceptions import OrderTypeError
from ppyt.rules import RuleBase
from ppyt.decorators import handle_nodataerror

logger = logging.getLogger(__name__)

class ConditionBase(RuleBase, metaclass=abc.ABCMeta):
    """conditions系の親クラスです。"""

    _rule_type = const.RULE_TYPE_CONDITIONS

    @handle_nodataerror(False)
    def can_entry(self, order_type, idx):
        """仕掛け可能かを判定します。

        Args:
            order_type: 購入種別
            idx: 日付を特定index

        Returns:
            仕掛け可能ならTrue、できないならFalse
        """
        if order_type == const.ORDER_TYPE_LONG:
            return self._can_entry_long(idx)
        elif order_type == const.ORDER_TYPE_SHORT:
            return self._can_entry_short(idx)
        else:
            raise OrderTypeError(order_type)

    def can_exit(self, order_type, idx):
        """手仕舞い可能かを判定します。

        Args:
            order_type: 購入種別
            idx: 日付を特定するindex

        Returns:
            手仕舞い可能ならTrue、できないならFalse
        """
        if order_type == const.ORDER_TYPE_LONG:
            return self._can_exit_long(idx)
        elif order_type == const.ORDER_TYPE_SHORT:
            return self._can_exit_short(idx)
        else:
            raise OrderTypeError(order_type)

    @abc.abstractmethod
    def _can_entry_long(self, idx):
        """買い仕掛け可能かを判定します。"""
        pass

    @abc.abstractmethod
    def _can_entry_short(self, idx):
        """売り仕掛け可能かを判定します。"""
        pass

    def _can_exit_long(self, idx):
        """買いの手仕舞いが可能かを判定します。"""
        # デフォルトは_can_entry_shortになります。
        return self._can_entry_short(idx)

    def _can_exit_short(self, idx):
        """売りの手仕舞いが可能かを判定します。"""
        # デフォルトは_can_entry_longになります。
        return self._can_entry_long(idx)


class ConditionTemplate(ConditionBase):
    """condition系クラスのテンプレートです。"""

    _findkey = 'テンプレート'  # conditionを一意に特定できる名前をつけます。

    def _setup(self):
        """初期化時に呼ばれます。パラメータ類を設定します。"""
        pass

    def _update(self):
        """銘柄を入れ替えたタイミングで呼ばれます。インスタンス変数を更新します。"""
        pass

    def _can_entry_long(self, idx):
        """買い仕掛けができるかを判定します。

        Args:
            idx: 日付を特定するindex

        Returns:
            仕掛けができる場合はTrue、できない場合はFalse
        """
        return False

    def _can_entry_short(self, idx):
        """売り仕掛けができるかを判定します。

        Args:
            idx: 日付を特定するindex

        Returns:
            仕掛けができる場合はTrue、できない場合はFalse
        """
        return False

    def _can_exit_long(self, idx):
        """買い注文に対する手仕舞いができるかを判定します。

        Args:
            idx: 日付を特定するindex

        Returns:
            手仕舞いができる場合はTrue、できない場合はFalse
        """
        return False

    def _can_exit_short(self, idx):
        """売り注文に対する手仕舞いができるかを判定します。

        Args:
            idx: 日付を特定するindex

        Returns:
            手仕舞いができる場合はTrue、できない場合はFalse
        """
        return False
