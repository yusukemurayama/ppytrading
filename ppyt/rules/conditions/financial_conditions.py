# coding: utf-8
import logging
from ppyt.rules.conditions import ConditionBase
from ppyt.models.orm import start_session, FinancialData

logger = logging.getLogger(__name__)


class AnnualOperatingCfIncreasingCondtion(ConditionBase):
    """営業キャッシュフローが増加しているかを判定します。"""
    _findkey = '年次営業キャッシュフロー増加エントリー'

    def _setup(self, percentage=None, years=None):
        """コンストラクタ

        Args:
            percentage: 毎年の増加率を指定します。
            years: 増加を確認する年数

        Raises:
            ArgumentError: 引数チェックに引っかかった場合に発生します。
        """
        self._is_valid_argument('percentage', percentage, int, float)
        self._is_valid_argument('years', years, int)

        self.rate = 1 + percentage * 0.01
        self.years = years

    def _update(self):
        """インスタンス変数を更新します。"""
        # FinancialDataをfiling_dateの降順で取得・設定します。
        with start_session(commit=False) as session:
            self.fd_list = session.query(FinancialData) \
                .filter_by(symbol=self.stock.symbol) \
                .filter_by(quarter=None) \
                .order_by(FinancialData.filing_date.desc()) \
                .all()

    def _can_entry_long(self, idx):
        # filing_dateが処理日以前のFinancialDataの一覧を取得します。
        sub_fd_list = [fd for fd in self.fd_list
                       if fd.filing_date <= self.get_date(idx)]

        year_count = 0  # 営業利益が増加した年数を保持する変数
        for i in range(self.years):
            try:
                fd1 = sub_fd_list[i]  # 年次のFinancialData
                fd2 = sub_fd_list[i + 1]  # 一つ前の年のFinancialData

                if fd1.cf_ope > 0 and fd1.cf_ope >= (fd2.cf_ope * self.rate):
                    # 営業利益がプラス
                    # かつ、営業利益が規定の数値分増加している場合
                    year_count += 1  # カウントを増やします。

            except IndexError:
                break

        return self.years == year_count

    def _can_entry_short(self, idx):
        # Long専用です。
        return False

    def _can_exit_long(self, idx):
        # Exitはチェックせずに全て通します。
        return True

    def _can_exit_short(self, idx):
        # Long専用です。
        return False
