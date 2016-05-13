# coding: utf-8
import logging
import csv
import os
from sqlalchemy import func
from ppyt import const
from ppyt.finders import SimpleFinder
from ppyt.exceptions import NoDataError, CommandError
from ppyt.commands import CommandBase
from ppyt.models.orm import start_session, Stock

logger = logging.getLogger(__name__)
plogger = logging.getLogger('print')


class Command(CommandBase):
    """indicatorをCSVに書き出すコマンドです。"""

    def _add_options(self, parser):
        """コマンド実行時の引数を定義します。"""
        # nargs='+'にしていないのは、指定されていないときにindicatorの一覧を表示するためです。
        parser.add_argument('indicators', type=str, nargs='*', default='')
        parser.add_argument('-s', '--symbol', type=str, default=None, required=False)
        parser.add_argument('-e', '--encoding', type=str, default='sjis', required=False)

    def _execute(self, options):
        """indicatorのエクスポートを実行します。
            使用例: ./manager.py export_indicators "移動平均線 span=25" "移動平均線 span=75"
        """
        if len(options.indicators) == 0:
            plogger.info('Usage: ./manager.py {} "findkey key=value key=value ..."  ...'.format(self._command))
            self._show_indicators()
            return

        self.encoding = options.encoding

        indicator_info_list = [self.__get_indicator_info_list(i) for i in options.indicators]

        for stock in self.__get_stocks(options.symbol):
            indicators = []
            for indicator_info in indicator_info_list:
                try:
                    indicators.append(indicator_info['class'](stock=stock, **indicator_info['kwds']))

                except TypeError as e:
                    msg = 'indicator[{}]のインスタンス生成に失敗しました。'.format(
                        indicator_info['str_indicator'])
                    raise CommandError(msg, e)

            # indicatorsをファイルに書き出します。
            self.__output(stock, indicators)

    def __get_indicator_info_list(self, str_indicator):
        """引数を元にして、出力するindicator関連の情報を格納したlistを取得します。

        Args:
            str_indicator: 出力するindicatorのstr
                例: 移動平均線 span=25
        """
        str_indicator = str_indicator.replace('　', ' ')  # 全角スペースを半角に置換しておきます。
        try:
            findkey, str_kwds = str_indicator.split(' ', 1)
        except ValueError:
            findkey, str_kwds = str_indicator, None

        klass, kwds = None, None
        klass = SimpleFinder.getinstance().find_class(const.RULE_TYPE_INDICATORS, findkey)
        if klass is None:
            raise CommandError('findkey[{}]に一致する指標が見つかりませんでした。'
                               .format(findkey))

        if str_kwds is not None:
            kwds = self._eqlist_to_dict(str_kwds.split(' '))
        plogger.info('検索キー: {}, キーワードパラメータ: {}'.format(findkey, kwds or 'なし'))

        return {'class': klass, 'kwds': kwds, 'str_indicator': str_indicator}

    def __get_stocks(self, symbol):
        """出力対象にする銘柄のリストを取得します。

        Args:
            symbol: 出力対象の銘柄のシンボル（Noneにした場合は全銘柄が対象になる）

        Returns:
            出力対象の銘柄を格納したリスト
        """
        with start_session() as session:
            q = session.query(Stock)
            if symbol:
                q = q.filter(func.lower(Stock.symbol) == symbol.lower())

            else:
                q = q.filter_by(activated=True)

            return q.all()

    def __output(self, stock, indicators):
        """historyデータやindicatorのデータを出力します。

        Args:
            stock: 出力対象の銘柄情報
            indicators: 出力するindicatorのリスト
        """
        filename = '-'.join([i.__class__.__name__ for i in indicators])
        output_path = os.path.join(const.OUTPUT_INDICATOR_DIR,
                                   '{}-{}.csv'.format(stock.symbol.lower(), filename))
        self._prepare_directory(os.path.dirname(output_path))

        headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        for i in indicators:
            headers.append(i.name_with_args)

        with open(output_path, 'w', encoding=self.encoding, newline='') as fp:
            w = csv.writer(fp)
            w.writerow(headers)
            for idx, hist in enumerate(stock.histories):
                row = [hist.date.strftime('%Y-%m-%d'),
                       hist.open_price,
                       hist.high_price,
                       hist.low_price,
                       hist.close_price,
                       hist.volume]
                for i in indicators:
                    try:
                        val = i.get(idx)
                        if isinstance(val, float):
                            # numpy.float64などはfloatにキャストしておきます。
                            # ※CSVに吐き出したときに桁が丸めこまれてしまったため。
                            val = float(val)
                    except NoDataError:
                        val = ''
                    row.append(val)
                w.writerow(row)

        plogger.info('[{}] にエクスポートしました。'.format(output_path))
