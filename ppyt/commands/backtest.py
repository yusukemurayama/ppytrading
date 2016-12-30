# coding: utf-8
import logging
import os
import shutil
from datetime import date, datetime
from sqlalchemy import func
from ppyt import const
from ppyt.commands import CommandBase
from ppyt.exceptions import CommandError
from ppyt.models.orm import Stock, start_session
from ppyt.trading_manager import BacktestManager

logger = logging.getLogger(__name__)
plogger = logging.getLogger('print')


class Command(CommandBase):
    """バックテストを実行するコマンドです。"""

    def _add_options(self, parser):
        """コマンド実行時の引数を定義します。"""
        parser.add_argument('rulefile', type=str, nargs='?', default=None)
        parser.add_argument('-s', '--symbol', type=str, required=False)
        parser.add_argument('-t', '--order-type', type=int, required=False)
        parser.add_argument('-S', '--start-year', type=int, required=False)
        parser.add_argument('-E', '--end-year', type=int, required=False)
        parser.add_argument('-o', '--output', action='store_true')

    def _execute(self, options):
        """バックテストを実行します。"""
        rulefile = options.rulefile or self._get_default_rulefile()
        logger.info('ルールは[{}]を使用します。'.format(rulefile))
        rules = self._get_rules(rulefile)
        logger.info('ルールファイル [{}] を処理します。'.format(options.rulefile))

        order_types = (options.order_type, ) if options.order_type in const.ORDER_TYPES else const.ORDER_TYPES
        logger.info('購入タイプ [{}] を処理します。'.format(
            ' / '.join(['LONG' if ot == const.ORDER_TYPE_LONG else 'SHORT' for ot in order_types])))

        start_date, end_date = None, None
        if options.start_year is not None:
            start_date = date(options.start_year, 1, 1)
        if options.end_year is not None:
            end_date = date(options.end_year, 12, 31)
        logger.info('期間 [{} 〜 {}] を処理します。'.format(
            *['指定なし' if not d else d.strftime('%Y-%m-%d') for d in [start_date, end_date]]))

        manager = BacktestManager(rulefile=options.rulefile,
                                  entry_groups=rules['entry_groups'],
                                  exit_groups=rules['exit_groups'],
                                  order_types=order_types)

        with start_session() as session:
            # activatedがTrueの銘柄が対象になるようにします。
            q = session.query(Stock).filter_by(activated=True)

            if options.symbol is not None:
                logger.info('銘柄 [{}] を対象とします。'.format(options.symbol))
                q = q.filter(func.lower(Stock.symbol) == options.symbol.lower())

            else:
                logger.info('全てのactivatedな銘柄を対象とします。')

            num_stocks = q.count()  # 対象銘柄数
            if num_stocks == 0:
                msg = '処理対象の銘柄が見つからないので処理を終了します。' + os.linesep
                msg += '先に、以下のコマンドで銘柄を絞り込んでください。' + os.linesep
                msg += './{} {}'.format(self._manager, 'filter_stocks')
                raise CommandError(msg)

            logger.info('処理対象銘柄は{:,d}件です。'.format(num_stocks))

            for i, stock in enumerate(q.all()):  # 処理対象の銘柄でループ
                plogger.info('{: 5,d} / {:,d} 件目を処理しています。'.format(
                    i + 1, num_stocks))
                stock.set_date(start_date, end_date)
                manager.set_stock(stock)
                manager.start()

        if options.output:  # 結果をファイルに出力するかを判定します。
            # 結果の出力先ディレクトリを決定、作成します。
            output_dir = os.path.join(const.OUTPUT_BACKTEST_DIR,
                                      datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-4])

            self._prepare_directory(output_dir)  # ディレクトリを作成します。

            manager.output(output_dir)  # バックテストの結果を保存します。

            # 使用したルールファイルを保存しておきます。
            shutil.copy(self._get_rulefilepath(options.rulefile),
                        os.path.join(output_dir, 'rule.json'))

            plogger.info('[{}] に結果が保存されました。'.format(output_dir))

        else:  # ファイルに出力しない場合は、全銘柄のサマリーを画面に表示します。
            plogger.info(manager.get_result())  # 全銘柄のサマリーを表示します。
