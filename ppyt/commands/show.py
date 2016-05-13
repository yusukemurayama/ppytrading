# coding: utf-8
import logging
import os
from ppyt.commands import CommandBase
from ppyt.models.orm import start_session, Sector, Stock

logger = logging.getLogger(__name__)
plogger = logging.getLogger('print')


class Command(CommandBase):
    """各種情報を表示するコマンドです。"""

    MODES = (  # これらをshowのあとに入力することで、処理モードが切り替わります。
        'sectors',
        'active_stocks',
        'indicators',
        'conditions',
        'entry_rules',
        'exit_rules',
        'filters'
    )

    def _add_options(self, parser):
        """コマンド実行時の引数を定義します。"""
        parser.add_argument('target', type=str, nargs='?', default='')

    def _execute(self, options):
        """有効な銘柄などを表示します。"""
        target = options.target
        if target in self.MODES:
            eval('self._show_' + target + '()')

        else:
            usage = '{}に続けて表示内容を指定してください。'.format(self._command) + os.linesep * 2
            usage += '# 表示内容' + os.linesep
            for m in self.MODES:
                usage += '- ' + m + os.linesep
            plogger.info(usage)

    def _show_active_stocks(self):
        """有効な銘柄を表示します。"""
        output = '# 有効な銘柄一覧' + os.linesep
        with start_session() as session:
            for s in session.query(Stock).filter_by(activated=True).all():
                output += '- ' + s.symbol + os.linesep
        plogger.info(output)

    def _show_sectors(self):
        """セクターの一覧を表示します。"""
        output = ''
        with start_session() as session:
            sectors = session.query(Sector).order_by('id').all()
            for sector in sectors:
                sector.cnt = session.query(Stock).filter_by(sector_id=sector.id).count()

        for sector in sorted(sectors, key=lambda s: s.cnt):
            output += '# ' + sector.name + os.linesep
            output += '- 作成日: ' + sector.created_at.strftime('%Y-%m-%d') + os.linesep
            output += '- 件数: {}'.format(sector.cnt) + os.linesep
            output += os.linesep

        plogger.info(output)
