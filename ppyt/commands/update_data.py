# coding: utf-8
import logging
import os
from datetime import datetime
from ppyt import const
from ppyt.commands import CommandBase
from ppyt.exceptions import CommandError
from ppyt.models.orm import start_session, Stock, History, FinancialData

logger = logging.getLogger(__name__)


class Command(CommandBase):
    """銘柄データや履歴データを登録・更新するコマンドです。"""

    # 処理モードを定義します。update_dataのあとに指定することで、その処理モードが実行されます。
    MODE_STOCK = 'stock'
    MODE_HISTORY = 'history'
    MODE_FINANCIAL = 'financial'
    MODE_ALL = 'all'
    MODES = (
        MODE_HISTORY,  # 銘柄情報更新モード
        MODE_STOCK,  # 履歴データ更新用モード
        MODE_FINANCIAL,  # Financial Data更新モード
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

        # symbolの一覧を取得します。
        with start_session() as session:
            self.symbols = [s.symbol for s in session.query(Stock).all()]

        if mode in (self.MODE_STOCK, self.MODE_FINANCIAL, self.MODE_ALL):  # Financial Data更新
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

            self.__import_histories_from_csv()

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
            for row in self._iter_rows_from_csvfile(filepath, as_dict=True):
                symbol = row['Symbol']
                name = row['Name']
                sector_name = row['Sector']
                Stock.save(session=session, name=name, symbol=symbol,
                           sector_name=sector_name, market_id=market_id)

        self._move_to_done_dir(filepath)  # importしたファイルを移動します。
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
                for row in self._iter_rows_from_csvfile(filepath, as_dict=True):
                    yield row

                self._move_to_done_dir(filepath)  # importしたファイルを移動します。

        logger.info('ファイナンシャルデータのインポートを開始しました。')
        skipped_symbols = set()
        with start_session(commit=True) as session:
            for row in iter_rows():
                logger.debug('row: {}'.format(row))
                symbol = row['Symbol']

                if symbol not in self.symbols:
                    logger.info('銘柄[{}]は登録されていません。'.format(symbol))
                    continue

                year = row['Year']
                quarter = row.get('Quarter')
                filing_date = datetime.strptime(row['Filing Date'], '%Y-%m-%d').date()
                revenue = row.get('Revenue')
                net_income = row.get('Net Income')
                cf_ope = row.get('Cash Flow From Operating Activities')
                cf_inv = row.get('Cash Flow From Investing Activities')
                cf_fin = row.get('Cash Flow From Financing Activities')

                q = session.query(Stock).filter_by(symbol=symbol)
                if not session.query(q.exists()).scalar():
                    skipped_symbols.add(symbol)
                    continue

                stock = q.one()
                FinancialData.save(session=session, stock=stock, year=year, quarter=quarter,
                                   filing_date=filing_date, revenue=revenue, net_income=net_income,
                                   cf_ope=cf_ope, cf_inv=cf_inv, cf_fin=cf_fin)

        if skipped_symbols:  # 登録できなかった銘柄があった場合
            logger.warn('stockテーブルにレコードがなかったため、'
                        '銘柄[{}]のファイナンシャルデータをインポートできませんでした。'
                        .format(', '.join(skipped_symbols)))

        logger.info('ファイナンシャルデータのインポートを終了しました。')

    def __import_histories_from_csv(self):
        """履歴関連のデータをCSVファイルから取得してインポートします。"""
        def generate_row():
            for filename in os.listdir(const.DATA_DIR_HISTORY):
                logger.info('ファイル[{}]をインポートします。'.format(
                    filename))
                filepath = os.path.join(const.DATA_DIR_HISTORY, filename)
                for row in self._iter_rows_from_csvfile(filepath, as_dict=True):
                    yield row

                self._move_to_done_dir(filepath)  # importしたファイルを移動します。
                logger.info('ファイル[{}]のインポートが完了しました。'.format(
                    filename))

        logger.info('履歴データインポートを開始しました。')

        for row in generate_row():
            with start_session(commit=True) as session:
                symbol = row['Symbol']
                date = datetime.strptime(row['Date'], '%Y-%m-%d').date()

                if symbol not in self.symbols:
                    logger.warn('銘柄[{}]は登録されていません。'.format(symbol))
                    continue

                logger.info('[Symbol: {}, Date: {:%Y-%m-%d}]を登録します。'.format(
                    symbol, date))

                History.save(session=session,
                             symbol=symbol,
                             date=date,
                             raw_close_price=row['Close'],
                             open_price=row['Adj. Open'],
                             high_price=row['Adj. High'],
                             low_price=row['Adj. Low'],
                             close_price=row['Adj. Close'],
                             volume=row['Adj. Volume'])

        logger.info('履歴データインポートを終了しました。')
