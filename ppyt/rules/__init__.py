# coding: utf-8
import logging
import abc
from ppyt import const
from ppyt.mixins import FinderMixin, ArgumentValidationMixin

logger = logging.getLogger(__name__)


class RuleBase(FinderMixin, ArgumentValidationMixin, metaclass=abc.ABCMeta):
    """ルール系（conditions, entry_rules, exit_rules）の基底クラスです。"""

    def __init__(self, *args, **kwds):
        """コンストラクタ
        ※このメソッドはオーバーライドせず、初期設定は_setupで実施してください。"""
        self._setup(*args, **kwds)

    def __str__(self):
        return self.__class__.__name__

    @abc.abstractmethod
    def _setup(self, *args, **kwds):
        """初期設定をします。サブクラスでオーバーライドして使います。

        Raises:
            ArgumentError: 引数チェックに引っかかった場合に発生します。
        """
        pass

    @abc.abstractmethod
    def _update(self):
        """インスタンス変数を更新します。サブクラスでオーバーライドして使います。"""
        pass

    def set_stock(self, stock):
        """銘柄情報を設定します。

        Args:
            stock: 銘柄情報
        """
        self.stock = stock
        self._update()

    def get_date(self, idx):
        """指定したindexが示す日付を取得します。

        Args:
            idx: 日付を決めるindex

        Returns:
            日付（datetime.date型オブジェクト）
        """
        return self.stock.get_date(idx)

    def get_price(self, idx, price_type=const.PRICE_TYPE_CLOSE):
        """指定したidxにおける各種の価格を取得します。

        Args:
            idx: 日付を決めるindex
            price_type: 取得する価格種別

        Returns:
            価格
        """
        return self.stock.get_price(idx, price_type)

    def get_open_price(self, idx):
        """指定したidxにおける始値を取得します。

        Args:
            idx: 日付を決めるindex

        Returns:
            始値
        """
        return self.stock.get_open_price(idx)

    def get_high_price(self, idx):
        """指定したidxにおける高値を取得します。

        Args:
            idx: 日付を決めるindex

        Returns:
            高値
        """
        return self.stock.get_high_price(idx)

    def get_low_price(self, idx):
        """指定したidxにおける安値を取得します。

        Args:
            idx: 日付を決めるindex

        Returns:
            安値
        """
        return self.stock.get_low_price(idx)

    def get_close_price(self, idx):
        """指定したidxにおける終値を取得します。

        Args:
            idx: 日付を決めるindex

        Returns:
            終値
        """
        return self.stock.get_close_price(idx)
