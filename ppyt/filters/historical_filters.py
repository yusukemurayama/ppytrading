# coding: utf-8
import logging
from sqlalchemy.sql import func
from ppyt.filters import FilterBase
from ppyt.models.orm import start_session, Stock, History

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

    def _filter_stock_ids(self, stock_ids):
        """銘柄を絞り込みます。

        絞り込み条件:
            - 過去の平均出来高が規定の値を上回っている。

        Args:
            stock_ids: 絞り込み前の銘柄IDのリスト

        Returns:
            絞り込み後の銘柄IDのリスト
        """
        filtered_stock_ids = []
        with start_session() as session:
            for s in session.query(Stock).all():
                if s.id not in stock_ids:
                    continue  # 既に除外されている銘柄はチェックしません。

                avg_volume = session.query(func.avg(History.volume)) \
                    .filter(History.stock_id == s.id).scalar()
                logger.debug('symbol - avg_volume: {} - {}'.format(
                    s.symbol, avg_volume))

                if avg_volume is not None and float(avg_volume) >= self.volume:
                    # 過去の平均出来高が規定値を上回っている場合、絞り込み後のリストに追加します。
                    filtered_stock_ids.append(s.id)

        return filtered_stock_ids
