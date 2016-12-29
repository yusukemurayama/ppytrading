# coding: utf-8
import logging
import csv
import os
import random
from datetime import date, timedelta
from itertools import chain
from ppyt import const
from ppyt.commands import CommandBase
from ppyt.exceptions import CommandError

logger = logging.getLogger(__name__)


class Command(CommandBase):
    """update_dataコマンドで取り込めるダミーデータを生成するコマンドです。"""

    DEFAULT_NUM_STOCKS = 50  # 作成する銘柄数のデフォルト値を定義します。
    DEFAULT_NUM_YEARS = 5  # 何年分のデータを作成するかのデフォルト値を定義します。

    def _add_options(self, parser):
        """コマンド実行時の引数を定義します。"""
        parser.add_argument('-n', dest='num_stocks', metavar='num_stocks',
                            type=int, default=self.DEFAULT_NUM_STOCKS)
        parser.add_argument('-y', dest='num_years', metavar='num_years',
                            type=int, default=self.DEFAULT_NUM_YEARS)
        parser.add_argument('-f', dest='force_flag', action='store_true')

    def _execute(self, options):
        """テスト用データを生成します。"""
        self.num_stocks = options.num_stocks
        self.num_years = options.num_years
        self._prepare_data_directories()
        self.__check_and_delete_files(options.force_flag)
        symbols = self.__create_stocklist()
        self.__create_financials(symbols)
        self.__create_historicals(symbols)

    def __check_and_delete_files(self, delete_flag=False):
        """データ保存先の存在をチェックします。"

        Args:
            delete_flag: Trueにしているとデータ保存先にあるファイルを削除します。

        Raises:
            CommandError: 既にファイルが存在する場合
        """
        for dirpath in const.DATA_SUB_DIRS:
            for fn in os.listdir(dirpath):
                if fn.startswith('.'):
                    continue
                if not delete_flag:
                    raise CommandError('ディレクトリ[{}]の中に既にファイル[{}]が'
                                       '存在しています。'.format(dirpath, fn))
                else:
                    filepath = os.path.join(dirpath, fn)
                    os.unlink(os.path.join(dirpath, fn))
                    logger.debug('filepath: [{}]を削除しました。'.format(filepath))

    def __create_stocklist(self):
        """テスト用銘柄をCSVファイルに書き出します。

        Returns:
            書きだしたテスト用銘柄のシンボルを格納したリスト
        """
        def get_row(idx):
            """CSVファイル1行の情報を取得します。"""
            return ('TEST{}'.format(idx),
                    'Test {}'.format(idx),
                    'Sector {}'.format(idx % 10),)

        header = ('Symbol', 'Name', 'Sector',)
        num_markets = len(const.MARKET_DATA.keys())
        lis = [[
            get_row(idx2) for idx2, row in enumerate(range(self.num_stocks))
            if idx2 % num_markets == idx1
        ] for idx1 in range(len(const.MARKET_DATA.keys()))]

        for idx, (market_id, market_name) in enumerate(const.MARKET_DATA.items()):
            with open(os.path.join(const.DATA_DIR_STOCKLIST, market_name + '.csv'), 'w',
                      encoding=const.DEFAULT_FILE_ENCODING, newline='') as fp:
                writer = csv.writer(fp, quoting=csv.QUOTE_ALL)
                writer.writerow(header)
                writer.writerows(lis[idx])

        return [row[0] for row in chain(*lis)]  # Symbolのリストを返します。

    def __create_financials(self, symbols):
        """テスト用のファイナンシャル情報をCSVファイルに書き出します。

        Args:
            symbols: 出力対象の銘柄情報のリスト
        """
        def get_rows(symbol, current_year):
            """CSVファイルのN行文のデータを取得します。"""
            def random_minus():
                return -1 if random.randint(0, 9) == 0 else 1

            def growing_rate():
                return random.randint(900, 1600) / 1000

            li = []
            start_year = current_year - self.num_years
            cf_ope = int(10**random.randint(6, 10) * random.random()) * random_minus()
            for idx in range(self.num_years):
                cf_ope = int(cf_ope * growing_rate() * random_minus())
                net_income = int(cf_ope * random.randint(5, 15) / 10 * random_minus())
                revenue = abs(int(net_income * random.randint(5, 20) / 10))
                cf_inv, cf_fin = None, None  # dummyデータではNoneにしておきます。
                li.append((symbol, start_year+idx, revenue, net_income, cf_ope, cf_inv, cf_fin))
            return li

        current_year = date.today().year
        header = ('Symbol', 'Year', 'Revenue', 'Net Income', 'Cash Flow From Operating Activities',
                  'Cash Flow From Investing Activities', 'Cash Flow From Financing Activities')
        rows = chain(*[get_rows(symbol, current_year) for symbol in symbols])

        with open(os.path.join(const.DATA_DIR_FINANCIAL, 'test.csv'), 'w',
                  encoding=const.DEFAULT_FILE_ENCODING, newline='') as fp:
            writer = csv.writer(fp, quoting=csv.QUOTE_ALL)
            writer.writerow(header)
            writer.writerows(rows)

    def __create_historicals(self, symbols):
        """テスト用の履歴データ（日付、始値等のデータ）をCSVファイルに出力します。

        Args:
            symbols: 出力対象の銘柄情報のリスト
        """
        def get_row(data, adjustment):
            """CSVファイル1行分のデータを取得します。"""
            p = 1.5  # 終値から最大で何ドル離れる可能性があるかを定義します。

            def random_price():
                return random.randint(-p*100, p*100) / 100

            li = [random_price(), random_price(), random_price()]
            li.sort()  # 金額が低い順に並び替えます。
            adj_close_price = data['close_price']
            adj_low_price = adj_close_price + li[0]
            adj_open_price = adj_close_price + li[1]
            adj_high_price = adj_close_price + li[2]
            adj_volume = random.randint(18**5, 10**7)
            ratio = adjustment / data['adjustment']
            open_price = adj_open_price * ratio
            high_price = adj_high_price * ratio
            low_price = adj_low_price * ratio
            close_price = adj_close_price * ratio
            volume = adj_volume * ratio

            if adj_close_price > adj_high_price:
                # 終値が高値を超えている場合は高値を終値に合わせます。
                adj_high_price = adj_close_price

            elif adj_close_price < adj_low_price:
                # 終値が安値ねを下回っている場合は安値を終値に合わせます。
                adj_low_price = adj_close_price

            return (data['date'],
                    round(open_price, 2),
                    round(high_price, 2),
                    round(low_price, 2),
                    round(close_price, 2),
                    volume,
                    round(adj_open_price, 2),
                    round(adj_high_price, 2),
                    round(adj_low_price, 2),
                    round(adj_close_price, 2),
                    adj_volume)

        header = ('Date', 'Open', 'High', 'Low', 'Close', 'Volume',
                  'Adj. Open', 'Adj. High', 'Adj. Low', 'Adj. Close', 'Adj. Volume')
        end_date = date.today() - timedelta(days=1)
        start_date = date(end_date.year-self.num_years+1, 1, 1)
        num_days = (end_date - start_date).days

        for symbol in symbols:
            close_price = random.randint(10000, 99999) / 100  # 終値を100.00から999.99の間で決めておきます。
            adjustment = 1
            adj_probability = 0.01  # 価格調整が入る確率（%）
            rows = []
            get_close_price = self.__get_close_price(close_price)

            for idx in range(num_days+1):
                close_price = get_close_price(close_price)
                rows.append({
                    'date': start_date + timedelta(days=idx),
                    'close_price': close_price,
                    'adjustment': adjustment,
                })

                if random.randint(0, 1 / (adj_probability / 10)) == 0:
                    logger.debug('adjustment: {}: {}'.format(symbol, adjustment))
                    adjustment *= 2

            with open(os.path.join(const.DATA_DIR_HISTORY, symbol.lower() + '.csv'), 'w',
                      encoding=const.DEFAULT_FILE_ENCODING, newline='') as fp:
                writer = csv.writer(fp, quoting=csv.QUOTE_ALL)
                writer.writerow(header)
                writer.writerows([get_row(d, adjustment) for d in rows])

    def __get_close_price(self, first_price, limit_param=4):
        """終値をランダム生成して取得します。

        Args:
            first_price: 最初の終値（この値から大きく乖離しないようにしている）
            limit_param: 生成する終値の範囲を決めるためのパラメータ
                最小はfirst_price / limit_param
                最大はfirst_price * limit_param
        """
        import random
        import math
        import bisect
        prices = [(idx + 1) / 100 for idx in range(500)]
        min_price, max_price = first_price / limit_param, first_price * limit_param
        scale = [math.log(x+2, len(prices)+1) for x in range(len(prices))]

        def inner(price):
            pos = bisect.bisect(scale, random.random())
            add_price = prices[pos]
            if min_price > price:
                pass
            elif max_price < price:
                add_price = -add_price
            elif random.randint(1, 1000) % 10 in (1, 2, 3, 4):
                add_price = -add_price
            return round(price + add_price, 2)
        return inner
