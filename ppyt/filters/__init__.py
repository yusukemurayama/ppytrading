# coding: utf-8
import logging
import abc
from ppyt.mixins import FinderMixin, ArgumentValidationMixin

logger = logging.getLogger(__name__)


class FilterBase(FinderMixin, ArgumentValidationMixin, metaclass=abc.ABCMeta):
    """フィルタ（銘柄絞り込み）の規定クラスです。"""

    def __init__(self, *args, **kwds):
        self._setup(*args, **kwds)

    @abc.abstractmethod
    def _setup(self, *args, **kwds):
        """初期化処理を行います。

        Args:
            foo: FOO
            bar: BAR

        Raises:
            ArgumentError: 引数チェックに引っかかった場合に発生します。
        """
        pass

    @abc.abstractmethod
    def _filter_stock_ids(self, stock_ids):
        """銘柄を絞り込みます。サブクラスでオーバーライドしてください。"""
        pass

    def get_stock_ids(self, stock_ids):
        """銘柄を絞り込みます。"""
        return self._filter_stock_ids(stock_ids)


class FilterTemplate(FilterBase):
    """フィルタクラスのテンプレートです。"""

    _findkey = 'テンプレート'  # フィルタを一意に特定できる名前をつけます。

    def _setup(self):
        """初期化処理を行います。"""
        pass

    def _filter_stock_ids(self, stock_ids):
        """銘柄を絞り込みます。

        絞り込み条件:
            - 条件1
            - 条件2
            - ...

        Args:
            stock_ids: 絞り込み前の銘柄IDのリスト

        Returns:
            絞り込み後の銘柄IDのリスト
        """
        pass
