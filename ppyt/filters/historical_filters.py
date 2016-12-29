# coding: utf-8
import logging
from sqlalchemy.sql import func
from ppyt.filters import FilterBase
from ppyt.models.orm import start_session, History

logger = logging.getLogger(__name__)


class AverageVolumeFilter(FilterBase):
    """平均出来形で銘柄を絞り込むクラスです。"""

    _findkey = '平均出来高フィルタ'  # フィルタを一意に特定できる名前をつけます。

    def _setup(self, volume=None):
        """初期化処理を行います。

        Args:
            volume: 平均出来高の閾値

        Raises:
            ArgumentError: 引数チェックに引っかかった場合に発生します。
        """
        self._is_valid_argument('volume', volume, int)

        self.volume = float(volume)

    def _filter_stocks(self, stocks):
        """銘柄を絞り込みます。

        絞り込み条件:
            - 過去の平均出来高が規定の値を上回っている。

        Args:
            stocks: 絞り込み前の銘柄のリスト

        Returns:
            絞り込み後の銘柄のリスト
        """
        filtered_stocks = []

        with start_session() as session:
            for s in stocks:
                avg_volume = session.query(func.avg(History.volume)) \
                    .filter_by(symbol=s.symbol).scalar()

                logger.debug('symbol - avg_volume: {} - {}'.format(
                    s.symbol, avg_volume))

                if avg_volume is not None and float(avg_volume) >= self.volume:
                    # 過去の平均出来高が規定値を上回っている場合、絞り込み後のリストに追加します。
                    filtered_stocks.append(s)

        return filtered_stocks
