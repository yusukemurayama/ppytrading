# coding: utf-8
import logging
import os
from ppyt.commands import CommandBase
from ppyt.models.orm import start_session, Stock, Setting

logger = logging.getLogger(__name__)
plogger = logging.getLogger('print')


class Command(CommandBase):
    """バックテストなどの対象になる銘柄を絞り込むコマンドです。"""

    def _add_options(self, parser):
        """コマンド実行時の引数を定義します。"""
        parser.add_argument('filterfile', type=str, nargs='?', default=None)

    def _execute(self, options):
        """銘柄の絞込を実行します。"""
        # 絞り込むルールを取得します。
        filterfile = options.filterfile \
            or Setting.get_value(Setting.KEY_DEFAULTFILTERFILE) or 'default'
        logger.info('フィルタは[{}]を使用します。'.format(filterfile))

        filters = self._get_stock_filters(filterfile)
        logger.debug('filters: {}'.format(filters))

        self.__filter_stocks(filters)  # フィルタで銘柄を絞り込みます。
        self.__update_stocks()  # 銘柄を更新します。
        self.__show()  # 絞り込み結果を表示します。

    def __filter_stocks(self, filters):
        """銘柄IDを絞り込みます。

        Args:
            filters: 絞り込みに使うfilterオブジェクトのリスト
        """
        with start_session() as session:
            # 最初は全ての銘柄をリストに入れておきます。
            stocks = list(session.query(Stock).order_by('symbol').all())

        for f in filters:
            # フィルタを使ってstock絞り込みます。
            stocks = f.get_stocks(stocks)
            logger.info('フィルタ[{}]によって[{}]に絞りこまれました。'.format(
                f.get_key(), ', '.join([str(s.symbol) for s in stocks])))

        self.stocks = stocks

    def __update_stocks(self):
        """銘柄情報のactivatedを更新します。"""
        # stockテーブルを更新します。
        filtered_symbols = [s.symbol for s in self.stocks]
        with start_session(commit=True) as session:  # 全銘柄でループ
            for s in session.query(Stock).order_by('symbol').all():
                s.activated = s.symbol in filtered_symbols

    def __show(self):
        text = '# 絞り込み結果: {:,d} 銘柄'.format(len(self.stocks)) + os.linesep
        for s in self.stocks:
            text += '- [{}] {}'.format(s.symbol, s.name) + os.linesep
        plogger.info(text)
