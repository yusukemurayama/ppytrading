# coding: utf-8
import logging
import os
from ppyt.commands import CommandBase
from ppyt.models.orm import start_session, Stock

logger = logging.getLogger(__name__)
plogger = logging.getLogger('print')


class Command(CommandBase):
    """バックテストなどの対象になる銘柄を絞り込むコマンドです。"""

    def _add_options(self, parser):
        """コマンド実行時の引数を定義します。"""
        parser.add_argument('filterfile', type=str, nargs='?', default='default')

    def _execute(self, options):
        """銘柄の絞込を実行します。"""
        # 絞り込むルールを取得します。
        filters = self._get_stock_filters(options.filterfile)
        logger.debug('filters: {}'.format(filters))

        self.__filter_stock_ids(filters)  # フィルタで銘柄を絞り込みます。
        self.__update_stocks()  # 銘柄を更新します。
        self.__show()  # 絞り込み結果を表示します。

    def __filter_stock_ids(self, filters):
        """銘柄IDを絞り込みます。

        Args:
            filters: 絞り込みに使うfilterオブジェクトのリスト
        """
        with start_session() as session:
            # 最初は全てのstock_idをリストに入れておきます。
            stock_ids = [s.id for s in session.query(Stock).order_by('id').all()]

        for f in filters:
            # フィルタを使ってstock_id絞り込みます。
            stock_ids = f.get_stock_ids(stock_ids)
            logger.info('フィルタ[{}]によって[{}]に絞りこまれました。'.format(
                f.get_key(), ', '.join([str(i) for i in stock_ids])))

        logger.debug('stock_ids: {}'.format(stock_ids))
        self.stock_ids = stock_ids

    def __update_stocks(self):
        """銘柄情報のactivatedを更新します。"""
        # stockテーブルを更新します。
        with start_session(commit=True) as session:  # 全銘柄でループ
            for s in session.query(Stock).order_by('id').all():
                s.activated = s.id in self.stock_ids

    def __show(self):
        text = '# 絞り込み結果' + os.linesep
        with start_session() as session:
            for stock_id in self.stock_ids:
                stock = session.query(Stock).get(stock_id)
                text += '- [{}] {}'.format(stock.symbol, stock.name) + os.linesep
        plogger.info(text)
