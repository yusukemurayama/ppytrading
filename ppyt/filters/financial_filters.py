# coding: utf-8
import logging
from collections import defaultdict
from ppyt.filters import FilterBase
from ppyt.models.orm import start_session, FinancialData

logger = logging.getLogger(__name__)


class CashFlowIncreasingFilter(FilterBase):
    """営業キャシュフローが毎年している銘柄を絞り込みます。"""

    _findkey = '営業キャッシュフローフィルタ'  # フィルタを一意に特定できる名前をつけます。

    def _setup(self, percentage=None, years=None):
        """初期化処理を行います。

        Args:
            percentage: 毎年の増加率を指定します。
            years: 過去何年間のデータを見るかを指定します。
                ここで指定した年数分のデータが揃っていない銘柄は、無条件で除外されます。

        Raises:
            ArgumentError: 引数チェックに引っかかった場合に発生します。
        """
        self._is_valid_argument('percentage', percentage, int, float)
        self._is_valid_argument('years', years, int)

        self.rate = 1 + percentage * 0.01
        self.years = years

    def _filter_stock_ids(self, stock_ids):
        """銘柄を絞り込みます。

        絞り込み条件:
            - years以上の過去データがある。
            - 毎年営業キャッシュフローがpercentage分増加している。

        Args:
            stock_ids: 絞り込み前の銘柄IDのリスト

        Returns:
            絞り込み後の銘柄IDのリスト
        """
        data = defaultdict(list)
        with start_session() as session:
            for fin in session.query(FinancialData).order_by('stock_id', 'year').all():
                if fin.stock_id not in stock_ids:
                    continue  # 既に除外されている銘柄はチェックしません。

                data[fin.stock_id].append(fin.cf_ope)

        def is_increasing(li):
            """listに含まれる値（営業キャッシュフロー）が後ろに行くごとに増加しているかを判定します。

            Args:
                li: 営業キャッシュフローが格納されたリスト

            Returns:
                増加していればTrue
            """
            if len(li) < self.years:
                return False

            pre_cf_ope = None
            for idx, cf_ope in enumerate(li):
                if idx > 0 and pre_cf_ope * self.rate > cf_ope:
                    return False  # 営業キャシュフローが増加していない場合はFalseを返します。

                pre_cf_ope = cf_ope  # 次のループのために、営業キャッシュフローを更新しておきます。

            return True

        return [stock_id for (stock_id, li) in data.items() if is_increasing(li)]
