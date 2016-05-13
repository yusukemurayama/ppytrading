# coding: utf-8
import logging
import os
from ppyt import const
from ppyt.models import Position, Result

logger = logging.getLogger(__name__)


class BacktestManager(object):
    """バックテストの実施を管理するクラスです。"""

    def __init__(self, rulefile, entry_groups, exit_groups,
                 order_types=const.ORDER_TYPES,
                 amount_per_trade=const.DEFAULT_AMOUNT_PER_TRADE):
        """コンストラクタ

        Args:
            rulefile: 使用するルールファイルの名前
            entry_groups: entry_group（仕掛け条件をまとめたdict）のリスト
            exit_groups: exit_group（仕掛け条件をまとめたdict）のリスト
            order_types: 実施する販売種別（LONG, SHORT）を含んだtuple
            amount_per_trade: 1トレード当たりで使う資金量
        """
        self.entry_groups = entry_groups
        self.exit_groups = exit_groups
        self.order_types = order_types
        self.amount_per_trade = amount_per_trade
        self.stock = None
        self.result = Result(rulefile)

    def set_stock(self, stock):
        """銘柄情報を設定します。

        Args:
            stock: 銘柄情報
        """
        import itertools
        self.stock = stock

        # conditoin, entry_rule, exit_ruleについても銘柄を入れ替えます。
        for rule in itertools.chain([eg['rule'] for eg in self.entry_groups],
                                    *[eg['conditions'] for eg in self.entry_groups],
                                    [eg['rule'] for eg in self.exit_groups],
                                    *[eg['conditions'] for eg in self.exit_groups]):
            rule.set_stock(stock)

    def start(self):
        """バックテストを実施します。"""
        # 保有している銘柄関連の情報を格納する変数を定義します。
        # ※テスト開始時は銘柄を保持していないのでNoneになります。
        position = None
        for idx, hist in enumerate(self.stock.histories):
            if position is not None:  # 前日からホールドしている場合
                # 昨日の情報に基づき、保有後の高値などを更新します。
                position.update(idx-1)

            if hist.volume == 0:
                # 出来高がない場合は、仕掛けも手仕舞いもできないようにします。
                continue

            if position is None:  # 株を保有していない場合
                entry_point = self.__get_entry_point(idx=idx)

                if entry_point is not None:
                    # 購入する株数を決める。
                    volume = int(self.amount_per_trade / entry_point['price'])

                    if volume == 0:
                        continue

                    if hist.volume < volume:
                        continue  # 実際にはhist.volume / 100 とかでも現実的ではないはず

                    # 注文可能な場合はポジションを立てます。
                    position = Position(stock=self.stock,
                                        order_type=entry_point['entry_group']['order_type'],
                                        entry_date=hist.date,
                                        entry_price=entry_point['price'],
                                        entry_timing=entry_point['timing'],
                                        entry_group=entry_point['entry_group'],
                                        volume=volume)

            if position is None:  # 株を保有していない場合
                continue

            # 手仕舞い情報を取得します。
            exit_point = self.__get_exit_point(position=position, idx=idx)

            if exit_point is not None:
                # 手仕舞う場合
                position.exit(
                    exit_date=hist.date, exit_price=exit_point['price'],
                    exit_timing=exit_point['timing'], exit_group=exit_point['exit_group'])
                self.result.add(position)
                position = None  # ポジションをクリアします。

    def get_result(self):
        """全銘柄合算のサマリーを表示します。"""
        return self.result.simple_result_md

    def output(self, output_dir, with_detail=True):
        """バックテストの結果を出力します。

        Args:
            output_dir: 出力先のディレクトリ
            with_detail: Trueにすると明細も出力されます。
        """
        # 全銘柄を合算した結果を出力します。
        with open(os.path.join(output_dir, 'total.md'), 'w',
                  encoding=const.DEFAULT_FILE_ENCODING) as fp:
            fp.write(self.result.get_result_md(stock=None))

        # 個別銘柄の結果を出力します。
        if with_detail:
            for s in self.result.stocks:
                detail_filepath = os.path.join(output_dir, s.symbol.lower() + '.md')
                with open(detail_filepath, 'w', encoding=const.DEFAULT_FILE_ENCODING) as fp:
                    fp.write(self.result.get_result_md(stock=s))

    def __get_entry_point(self, idx):
        """仕掛けに関する情報をdict型で取得します。
        なお、仕掛ける条件を満たしていない場合はNoneが返ります。

        Args:
            idx: 日付を決めるindex

        Retruns:
            dict:
                entry_group: 仕掛け関連の情報をまとめたdict型オブジェクト
                timing: 仕掛けるタイミング
                prince: 仕掛ける値段
        """
        for eg, entry_timing in self.__iter_entry_groups(idx):
            order_type = eg['order_type']
            rule = eg['rule']

            if not rule.is_timing_matched(entry_timing):
                continue

            price = rule.get_entry_price(order_type=order_type, idx=idx, timing=entry_timing)

            if price is not None:  # 仕掛けの条件に達していた場合
                return {'entry_group': eg, 'timing': entry_timing, 'price': price}

        # 全ての時間帯、条件で仕掛けができない場合
        return None

    def __iter_entry_groups(self, idx):
        """すべてのconditionを満たした仕掛け情報を取得します。

        Args:
            idx: 日付を決めるindex

        Yields:
            仕掛け情報が入ったdict
            仕掛けるタイミング
        """
        for eg in self.entry_groups:
            order_type = eg['order_type']

            if order_type not in self.order_types:
                # 購入タイプ（LONG or SHORT）が処理対象ではない場合
                continue

            if not all([cond.can_entry(order_type=order_type, idx=idx) for cond in eg['conditions']]):
                # 1つでもエントリーできない条件が見つかった場合
                continue

            for entry_timing in const.ORDER_TIMINGS:
                yield eg, entry_timing

    def __get_exit_point(self, position, idx):
        """手仕舞いに関する情報をdict型で取得します。
        なお、手仕舞い条件を満たしていない場合はNoneが返ります。
        """
        for eg, exit_timing in self.__iter_exit_groups(position, idx):
            rule = eg['rule']

            if not rule.is_timing_matched(exit_timing):
                continue

            price = rule.get_exit_price(position=position, idx=idx, timing=exit_timing)

            if price is not None:  # 手仕舞う条件に達していた場合
                return {'exit_group': eg, 'timing': exit_timing, 'price': price}

        # 手仕舞い条件に達していない場合はNoneを返します。
        return None

    def __iter_exit_groups(self, position, idx):
        """すべてのconditionを満たした手仕舞いに関する情報を取得します。

        Args:
            position: 保有しているポジション情報
            idx: 日付を決めるindex

        Yields:
            手仕舞い情報が入ったdict
            手仕舞いタイミング
        """
        order_type = position.order_type
        for eg in self.exit_groups:
            if order_type != eg['order_type']:
                continue

            if not all([cond.can_exit(order_type=order_type, idx=idx) for cond in eg['conditions']]):
                continue

            for exit_timing in self.__get_exit_timings(position):
                yield eg, exit_timing

    def __get_exit_timings(self, position):
        """手仕舞いできるタイミングをtuple型で取得します。

        Args:
            position: 保有中のポジション情報

        Returns:
            手仕舞いできるタイミングのtuple
        """
        if position.period == 0:  # 売買当日の場合
            return tuple(ot for ot in const.ORDER_TIMINGS if ot > position.entry_timing)

        else:  # 売買当日以降
            return const.ORDER_TIMINGS
