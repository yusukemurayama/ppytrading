# coding: utf-8
import logging
import os
from datetime import datetime
from ppyt import const
from ppyt.commands import CommandBase
from ppyt.exceptions import CommandError
from ppyt.models.orm import start_session, Stock, HistoryBase, FinancialData

logger = logging.getLogger(__name__)


class Command(CommandBase):
    """銘柄データや履歴データを登録・更新するコマンドです。"""

    # 処理モードを定義します。update_dataのあとに指定することで、その処理モードが実行されます。
    MODE_STOCK = 'stock'
    MODE_HISTORY = 'history'
    MODE_ALL = 'all'
    MODES = (
        MODE_HISTORY,  # 銘柄情報更新モード
        MODE_STOCK,  # 履歴データ更新用モード
        MODE_ALL,  # 全実行モード
    )

    def _add_options(self, parser):
        """コマンド実行時の引数を定義します。"""
        parser.add_argument('mode', type=str, nargs='?', default=self.MODE_HISTORY)

    def _execute(self, options):
        """銘柄などの情報を更新します。"""
        mode = options.mode
        logger.info('{}モードで起動します。'.format(mode))

        if mode not in self.MODES:
            print('処理モードを正しく指定してください。')
            print('処理モード:')
            for m in self.MODES:
                suffix = ' [default]' if m == self.MODE_HISTORY else ''
                print('  - {}{}'.format(m, suffix))
            exit()

        if mode in (self.MODE_STOCK, self.MODE_ALL):  # 銘柄更新
            for market_id in const.MARKET_DATA.keys():
                self.__import_stock_list_from_csv(market_id)

            self.__import_financial_data_from_csv()

        if mode in (self.MODE_HISTORY, self.MODE_ALL):  # ヒストリカルデータ更新
            with start_session() as session:
                stocks = session.query(Stock).all()

                if len(stocks) == 0:
                    msg = '銘柄が登録されていません。先に' + os.linesep
                    msg += './{} {} {}'.format(self._manager,
                                               self._command, self.MODE_STOCK) + os.linesep
                    msg += 'を実行して銘柄情報を取り込んでください。'
                    raise CommandError(msg)

            for stock in stocks:
                self.__import_histories_from_csv(stock)

    def __import_stock_list_from_csv(self, market_id):
        """銘柄情報をCSVファイルから取得してインポートします。

        Args:
            market_id: 取り込み対象のマーケットID
        """
        filename = const.MARKET_DATA[market_id] + '.csv'
        market_name = const.MARKET_DATA[market_id]
        logger.info('マーケット[{}]の銘柄リストのインポートを開始しました。'.format(market_name))
        filepath = os.path.join(const.DATA_DIR_STOCKLIST, filename)

        if not os.path.isfile(filepath):
            raise CommandError('銘柄リスト[{}]のインポートに失敗しました。'
                               'ファイルが存在ません。'.format(filepath))

        with start_session(commit=True) as session:
            for row in self._iter_rows_from_csvfile(filepath):
                symbol = row[0]
                name = row[1]
                sector_name = row[2]
                Stock.save(session=session, name=name, symbol=symbol,
                           sector_name=sector_name, market_id=market_id)

        logger.info('マーケット[{}]の銘柄リストのインポートを終了しました。'.format(market_name))

    def __import_financial_data_from_csv(self):
        """ファイナンシャルデータをCSVファイルから取得してインポートします。"""
        def iter_rows():
            """CSVファイルを読み込み、インポートする情報を取得します。

            Yields:
                CSVファイルの1行のデータ
            """
            dirpath = const.DATA_DIR_FINANCIAL
            for filename in os.listdir(dirpath):
                if os.path.splitext(filename)[1] != '.csv':
                    continue
                filepath = os.path.join(dirpath, filename)
                for row in self._iter_rows_from_csvfile(filepath):
                    yield row

        logger.info('ファイナンシャルデータのインポートを開始しました。')
        skipped_symbols = set()
        with start_session(commit=True) as session:
            for row in iter_rows():
                logger.debug('row: {}'.format(row))
                symbol, year, revenue, net_income, cf_ope, cf_inv, cf_fin = row
                q = session.query(Stock).filter_by(symbol=symbol)
                if not session.query(q.exists()).scalar():
                    skipped_symbols.add(symbol)
                    continue

                stock = q.one()
                FinancialData.save(session=session, stock=stock,
                                   year=year, revenue=revenue, net_income=net_income,
                                   cf_ope=cf_ope, cf_inv=cf_inv, cf_fin=cf_fin)

        if skipped_symbols:  # 登録できなかった銘柄があった場合
            logger.warn('stockテーブルにレコードがなかったため、'
                        '銘柄[{}]のファイナンシャルデータをインポートできませんでした。'
                        .format(', '.join(skipped_symbols)))

        logger.info('ファイナンシャルデータのインポートを終了しました。')

    def __import_histories_from_csv(self, stock):
        """履歴関連のデータをCSVファイルから取得してインポートします。

        Args:
            stock: インポート対象の銘柄情報
        """
        logger.info('Symbol [{}] の履歴データインポートを開始しました。'.format(stock.symbol))
        filepath = os.path.join(const.DATA_DIR_HISTORY, '{}.csv'.format(stock.symbol.lower()))
        logger.debug('filepath: {}'.format(filepath))

        if not os.path.isfile(filepath):
            if stock.activated:  # 銘柄が使用中の場合は例外を投げます。
                msg = 'ファイル: [{}]は存在しないので' \
                    'データをインポートできませんでした。'.format(filepath)
                raise CommandError(msg)

            # 銘柄が使用中でない場合は、ファイルが無くても処理を続けます。
            logger.info('[{}]は見つかりませんでした。'.format(filepath))
            return

        HistoryBase.create_table(stock)  # テーブルがまだない場合は作成します。
        History = HistoryBase.get_class(stock)
        History = HistoryBase.get_class(stock)

        with start_session(commit=True) as session:
            for row in self._iter_rows_from_csvfile(filepath):
                str_date, raw_open_price, raw_high_price, raw_low_price, \
                    raw_close_price, volume, close_price = row

                date = datetime.strptime(str_date, '%Y-%m-%d').date()
                History.save(session=session, date=date,
                             raw_open_price=raw_open_price,
                             raw_high_price=raw_high_price,
                             raw_low_price=raw_low_price,
                             raw_close_price=raw_close_price,
                             close_price=close_price,
                             volume=volume)
        logger.info('Symbol [{}] の履歴データインポートを終了しました。'.format(stock.symbol))