# coding: utf-8
import logging
from ppyt import const
from ppyt.rules.exit_rules import ExitBase
from ppyt.indicators.basic_indicators import MovingAverageIndicator

logger = logging.getLogger(__name__)


class SimpleExit(ExitBase):
    """（conditionsを覗いて）条件なしで手仕舞うクラスです。"""
    _findkey = '条件なし'  # exit_ruleを一意に特定できる名前をつけます。

    def _setup(self):
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
        if timing == const.ORDER_TIMING_OPEN:
            return self.get_open_price(idx)
        elif timing == const.ORDER_TIMING_SESSION:
            return None
        elif timing == const.ORDER_TIMING_CLOSE:
            return self.get_close_price(idx)

    def _get_exit_price_short(self, position, idx, timing):
        """売りポジションに対する手仕舞い価格を取得します。

        Args:
            position: 保有中のポジション情報
            idx: 日付を特定するindex
            timing: 注文タイミング

        Returns:
            手仕舞う価格（手仕舞わない場合はNoneを返す）
        """
        if timing == const.ORDER_TIMING_OPEN:
            return self.get_open_price(idx)
        elif timing == const.ORDER_TIMING_SESSION:
            return None
        elif timing == const.ORDER_TIMING_CLOSE:
            return self.get_close_price(idx)


class TrailingStop(ExitBase):
    """保有後の高値・安値から規定％分利益が減る方向に進んだら手仕舞うクラスです。"""
    _findkey = 'トレーリングストップ'  # exit_ruleを一意に特定できる名前をつけます。

    def _setup(self, percentage=None):
        """初期化時に呼ばれます。パラメータ類を設定します。"""
        self._is_valid_argument('percentage', percentage, int, float)

        self.rate_long = 1.0 - percentage * 0.01
        self.rate_short = 1.0 + percentage * 0.01

    def _update(self):
        """銘柄を入れ替えたタイミングで呼ばれます。インスタンス変数を更新します。"""
        pass

    def _get_exit_price_long(self, position, idx, timing):
        """買いポジションに対する手仕舞い価格を取得します。

        手仕舞い:
            - ザラ場中に手仕舞う。
            - 保有後の高値から、規定の%分下がったら手仕舞う。

        Args:
            position: 保有中のポジション情報
            idx: 日付を特定するindex
            timing: 注文タイミング

        Returns:
            手仕舞う価格（手仕舞わない場合はNoneを返す）
        """
        if position.high_price is None:
            return None  # 仕掛け直後はスルーします。

        if timing != const.ORDER_TIMING_SESSION:
            return None  # ザラ場中以外はスルーします。

        exit_price = position.high_price * self.rate_long
        if exit_price >= self.get_low_price(idx):
            # 直近高値よりも規定の%下回っている場合は手仕舞います。
            return exit_price
        return None

    def _get_exit_price_short(self, position, idx, timing):
        """売りポジションに対する手仕舞い価格を取得します。

        手仕舞い:
            - ザラ場中に手仕舞う。
            - 保有後の安値から、規定の%分上がったら手仕舞う。

        Args:
            position: 保有中のポジション情報
            idx: 日付を特定するindex
            timing: 注文タイミング

        Returns:
            手仕舞う価格（手仕舞わない場合はNoneを返す）
        """
        if position.low_price is None:
            return None  # 仕掛け直後はスルーします。

        if timing != const.ORDER_TIMING_SESSION:
            return None  # ザラ場中以外はスルーします。

        exit_price = position.low_price * self.rate_short
        if exit_price <= self.get_high_price(idx):
            # 直近安値よりも規定の%上回っている場合は手仕舞います。
            return exit_price
        return None


class PriceAndMovingAverageExit(ExitBase):
    _findkey = '価格が移動平均線を抜けたら手仕舞い'

    def _setup(self, span, price_type_long=const.PRICE_TYPE_CLOSE,
               price_type_short=const.PRICE_TYPE_CLOSE):
        self._is_valid_argument('span', span, int)

        self.span = span
        self.price_type_long = price_type_long
        self.price_type_short = price_type_short
        self.timing = const.ORDER_TIMING_OPEN  # 寄り付きのみを有効とします。

    def _update(self):
        self.moving_average = MovingAverageIndicator(stock=self.stock, span=self.span)

    def _get_exit_price_long(self, position, idx, timing):
        # 前日の価格が移動平均を下に抜けたら、当日の始値で手仕舞いします。
        if self.moving_average.get(idx-1) > self.get_price(idx-1, self.price_type_long):
            return self.get_open_price(idx)
        return None

    def _get_exit_price_short(self, position, idx, timing):
        # 前日の価格が移動平均を上に抜けたら、当日の始値で手仕舞いします。
        if self.moving_average.get(idx-1) < self.get_price(idx-1, self.price_type_short):
            return self.get_open_price(idx)
        return None


class PeriodBasedExit(ExitBase):
    _findkey = '日数経過で手仕舞い'

    def _setup(self, period=None):
        self._is_valid_argument('period', period, int)

        self.period = period

    def _update(self):
        pass

    def _get_exit_price_long(self, position, idx, timing):
        if timing == const.ORDER_TIMING_OPEN:
            if position.period >= self.period:
                return self.get_open_price(idx)
        return None

    def _get_exit_price_short(self, position, idx, timing):
        return self._get_exit_price_long(position, idx, timing)
