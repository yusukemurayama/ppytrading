# coding: utf-8
import logging
import os
from ppyt import const
from ppyt.decorators import cached_property
from ppyt.utils import format_for_date, format_with_comma
from ppyt.utils import format_with_padding

logger = logging.getLogger(__name__)


class Position(object):
    """仕掛けから手仕舞いまでに関する情報を保持します。"""

    def __init__(self, stock, order_type, entry_date, entry_price,
                 entry_timing, entry_group, volume):
        """コンストラクタ

        Args:
            stock: 銘柄
            order_type: 購入種別（買い or 売り）
            entry_date: 仕掛けた日
            entry_price: 仕掛けた価格
            entry_timing: 仕掛けたタイミング
            volume: 仕掛けた株数
        """
        self.stock = stock
        self.order_type = order_type
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.entry_timing = entry_timing
        self.entry_group = entry_group  # 仕掛けに使ったルールなどを設定しておきます。
        self.volume = volume

        # 手仕舞い系のインスタンス変数をNoneに設定しておきます。
        self.exit_date = None
        self.exit_price = None
        self.exit_timing = None
        self.high_price = None
        self.low_price = None

        self.period = 0  # 保有期間を0にしておきます。

    @property
    def is_order_long(self):
        """保有中の銘柄が買い注文だったのかを取得します。"""
        return self.order_type == const.ORDER_TYPE_LONG

    @property
    def is_order_short(self):
        """保有中の銘柄が売り注文だったのかを取得します。"""
        return self.order_type == const.ORDER_TYPE_SHORT

    @property
    def profit(self):
        """利益を取得します。"""
        if self.exit_price is None:
            raise Exception('まだ手仕舞いしていないため計算できません。')

        if self.is_order_long:  # 買い
            return (self.exit_price - self.entry_price) * self.volume
        else:  # 売りの場合
            return (self.entry_price - self.exit_price) * self.volume

    @property
    def return_rate(self):
        """仕掛け価格に対する利益を取得します。損失発生時はマイナスになります。"""
        if self.is_order_long:  # 買い
            return (self.exit_price - self.entry_price) / self.entry_price
        else:  # 売り
            return (self.entry_price - self.exit_price) / self.entry_price

    @property
    def year(self):
        """取引が完了した年を取得します。集計の時に使います。"""
        return self.exit_date.strftime('%Y')

    def update(self, idx):
        """ポジションを更新します。

        Args:
            idx: 日付を特定できるindex
        """
        # 高値、安値を取得します。
        high_price = self.stock.get_high_price(idx)
        low_price = self.stock.get_low_price(idx)

        if self.high_price is None:
            # 保有中の高値が未設定の場合、高値を更新します。
            self.high_price = high_price
        else:
            # 保有中の高値を更新します。
            self.high_price = max(self.high_price, high_price)

        if self.low_price is None:
            # 保有中の安値が未設定の場合、安値を更新します。
            self.low_price = low_price
        else:
            # 保有中の安値を更新します。
            self.low_price = min(self.low_price, low_price)

        self.period += 1  # 保有期間を増やします。

    def exit(self, exit_date, exit_price, exit_timing, exit_group):
        """手仕舞います。

        Args:
            exit_date: 手仕舞う日
            exit_timing: 手仕舞うタイミング
            exit_group: 手仕舞いに使ったルールなどの情報
        """
        self.exit_date = exit_date
        self.exit_price = exit_price
        self.exit_timing = exit_timing
        self.exit_group = exit_group


class Result(object):
    """トレード結果を保持するクラスです。
    仕掛けから手仕舞いまで終わったポジション情報を複数持ちます。"""

    def __init__(self, rulefile):
        """コンストラクタ

        Args:
            rulefile: 使用するルールファイルのファイル名
        """
        self.positions = []
        self.rulefile = rulefile

    @property
    def stocks(self):
        """トレードが完了した銘柄一覧を取得します。"""
        return {pos.stock.id: pos.stock for pos in self.positions}.values()

    @property
    def simple_result_md(self):
        """トレード結果の概要をMarkdown形式の文字列で取得します。"""
        text = '''# 全銘柄合算
## 使用ルールファイル
{rule}

## サマリー
{summary}
'''
        return text.format(rule=self.rulefile,
                           summary=self.__get_summary_table_md(self.positions))

    def add(self, position):
        """終了したポジションを追加します。"""
        self.positions.append(position)

    def get_result_md(self, stock=None):
        """集計結果を取得します。

        Args:
            stock: 銘柄情報（指定しない場合は全銘柄の合算値）
        Returns:
            集計結果の文字列（Markdown）
        """
        output = ''

        # 銘柄指定の場合は、対象の銘柄で絞り込みます。
        positions = [pos for pos in self.positions if stock.id == pos.stock.id] if stock else self.positions

        # サマリーを追加します。
        output += self.__get_summary_md(positions)

        # 明細を追加します。
        output += self.__get_detail_md(positions)

        return output

    def __get_summary_md(self, positions):
        """集計結果のサマリーを取得します。

        Args:
            positions: 集計対象のポジション情報を含むリスト

        Returns:
            集計結果のサマリーの文字列（Markdown）
        """
        fmt = '''# サマリー
## 全期間の合算
{entire}

## 年毎
{annual}'''
        annual = ''
        annual_position_data = self.__get_annual_position_data(positions)
        for year in sorted(annual_position_data.keys()):
            annual += '### {}年'.format(year) + os.linesep
            annual += self.__get_summary_table_md(annual_position_data[year])
            annual += os.linesep * 2  # 各年度の下は1行空けます。

        return fmt.format(entire=self.__get_summary_table_md(positions),
                          annual=annual).strip() + os.linesep * 2

    def __get_annual_position_data(self, positions):
        """「key: 手仕舞った年、value: ポジション情報のリスト」のdict型オブジェクトを取得します。"""
        yearset = set([pos.year for pos in positions])
        return {year: [pos for pos in positions if pos.year == year] for year in yearset}

    def __get_summary_table_md(self, positions):
        """サマリーに表示する1つのテーブル部分を取得します。

        Args:
            positions: 集計対象のポジション情報を含むリスト

        Returns:
            集計結果のサマリーの文字列（Markdown）
        """
        COL_WIDTH = 35  # テーブルの横幅の文字数を定義します。
        summary = self.Summary(positions)

        if summary.num_trades == 0:
            return '手仕舞いまで進んだトレードはありませんでした。'

        def get_line(label, value, currency=False, with_comma=False, percentage=False):
            """テーブルの1行分の文字列を取得します。

            Args:
                label: テーブルの左側に入る値
                value: テーブルの右側に入る値
                currency: Trueにすると通過表示になります。
                with_comman: Trueにすると3桁カンマで句切られます。
                percentage: %形式にします。
            """
            if currency:
                # value = locale.currency(value, grouping=True)
                value = '{:.2f}'.format(value)
                if value.startswith('-'):  # 金額がマイナスの場合
                    value = '-$' + value[1:]
                else:
                    value = '$' + value
            elif percentage:
                value = '{:.2%}'.format(value)
            elif with_comma:
                value = format_with_comma(value)

            label = format_with_padding(label, COL_WIDTH, align='l')
            value = format_with_padding(value, COL_WIDTH, align='r')
            return '|{}|{}|'.format(label, value) + os.linesep

        # Markdown形式でテーブルを組み立てます。
        text = ''
        text += '|{}|{}|'.format(
            format_with_padding('項目', COL_WIDTH, align='c'),
            format_with_padding('数値', COL_WIDTH, align='c')) + os.linesep
        text += '|{}|{}|'.format(
            '-' * COL_WIDTH, ':'.rjust(COL_WIDTH, '-')) + os.linesep
        text += get_line('平均リターン（$100辺り）', summary.avg_return_rate*100, currency=True)
        text += get_line('ペイオフレシオ', summary.str_payoff_ratio)
        text += get_line('勝率', summary.win_rate, percentage=True)
        text += get_line('総トレード数', summary.num_trades)
        text += get_line('最大勝ちリターン（$100辺り）', summary.max_return_rate*100, currency=True)
        text += get_line('最大負けリターン（$100辺り）', summary.min_return_rate*100, currency=True)
        text += get_line('勝ちトレード数', summary.num_wins)
        text += get_line('負けトレード数', summary.num_loses)
        text += get_line('平均保有期間', summary.avg_periods, with_comma=True)
        """
        text += get_line('合計利益', summary.profit)
        text += get_line('平均利益（勝ちトレード）', summary.avg_profit_wins)
        text += get_line('平均損失（負けトレード）', summary.avg_profit_loses)
        """

        return text.strip()

    def __get_detail_md(self, positions):
        """各トレードの明細を取得します。

        Args:
            positions: 集計対象のポジション情報を含むリスト

        Retusn:
            集計結果の明細の文字列（Markdown）
        """
        ptn = '''# 明細
{detail}'''

        detail = '''
| 区分 | 開始日 | 開始価格 | 時間 | 終了日 | 終了価格 | 時間 | 数量 | 利益 | 利益率 |
|------|:------:|---------:|:----:|:------:|---------:|:----:|-----:|-----:|-------:|
'''

        def str_order_timing(order_timing):
            return const.ORDER_TIMING_DATA.get(order_timing, '不明')

        for pos in positions:
            detail += '|' + '|'.join([
                '買い' if pos.is_order_long else '売り',
                format_for_date(pos.entry_date),
                format_with_comma(pos.entry_price),
                str_order_timing(pos.entry_timing),
                format_for_date(pos.exit_date),
                format_with_comma(pos.exit_price),
                str_order_timing(pos.exit_timing),
                format_with_comma(pos.volume),
                format_with_comma(pos.profit),
                '{:.2%}'.format(pos.return_rate),
            ]) + '|' + os.linesep

        return ptn.format(detail=detail.strip()).strip()

    class Summary(object):
        """ポジション情報を集計するためのクラスです。"""

        def __init__(self, positions):
            """コンストラクタ

            Args:
                positions: 集計対象となるポジション情報のリスト
            """
            self.positions = positions

        @cached_property
        def positions_win(self):
            """勝ったポジション情報を取得します。"""
            return [pos for pos in self.positions if pos.profit > 0]

        @cached_property
        def positions_lose(self):
            """負けたポジション情報を取得します。"""
            return [pos for pos in self.positions if pos.profit < 0]

        @cached_property
        def profit(self):
            """利益合計を取得します。"""
            return sum([pos.profit for pos in self.positions])

        @cached_property
        def profit_wins(self):
            """勝ったトレードの利益合計を取得します。"""
            return sum([pos.profit for pos in self.positions_win])

        @cached_property
        def profit_loses(self):
            """負けたトレードの損失合計を取得します。
            ※負けたトレードがあればマイナスの数値が返ります。"""
            return sum([pos.profit for pos in self.positions_lose])

        @cached_property
        def periods(self):
            """ポジションを立てていた期間の合計を取得します。"""
            return sum([pos.period for pos in self.positions])

        @cached_property
        def num_trades(self):
            """トレード回数の合計を取得します。"""
            return len(self.positions)

        @cached_property
        def num_wins(self):
            """勝ったトレードの回数を取得します。"""
            return len(self.positions_win)

        @cached_property
        def num_loses(self):
            """負けたトレードの回数を取得します。"""
            return len(self.positions_lose)

        @cached_property
        def num_draws(self):
            """引き分けだったトレードの回数を取得します。"""
            return len([pos for pos in self.positions if pos.profit == 0])

        @cached_property
        def win_rate(self):
            return self.num_wins / self.num_trades if self.num_trades else 0

        @cached_property
        def avg_profit(self):
            """利益の平均を取得します。"""
            return self.profit / self.num_trades if self.num_trades else 0

        @cached_property
        def avg_profit_wins(self):
            """勝ったトレードの利益の平均を取得します。"""
            return self.profit_wins / self.num_wins if self.num_wins else 0

        @cached_property
        def avg_profit_loses(self):
            """負けたトレードの損失の平均を取得します。
            ※負けたトレードがある場合はマイナスの数値が返ります。"""
            return self.profit_loses / self.num_loses if self.num_loses else 0

        @cached_property
        def avg_periods(self):
            """平均保有期間を取得します。"""
            return self.periods / self.num_trades if self.num_trades else 0

        @cached_property
        def payoff_ratio(self):
            """ペイオフレシオ（平均利益 / 平均損失）の絶対値を取得します。"""
            return abs(self.avg_profit_wins / self.avg_profit_loses) if self.avg_profit_loses else None

        @cached_property
        def str_payoff_ratio(self):
            """ペイオフレシオを文字列で取得します。"""
            return str(round(self.payoff_ratio, 2)) if self.payoff_ratio is not None else const.NAN

        @cached_property
        def avg_return_rate(self):
            """仕掛け価格に対する利益をの平均を取得します。"""
            return sum([pos.return_rate for pos in self.positions]) / self.num_trades if self.num_trades else None

        @cached_property
        def max_return_rate(self):
            """仕掛け価格に対する利益の最大値（一番勝ったトレード）を取得します。 """
            return max([pos.return_rate for pos in self.positions_win]) if self.positions_win else 0

        @cached_property
        def min_return_rate(self):
            """仕掛け価格に対する利益の最小値（一番負けたトレード）を取得します。 """
            return min([pos.return_rate for pos in self.positions_lose]) if self.positions_lose else 0
