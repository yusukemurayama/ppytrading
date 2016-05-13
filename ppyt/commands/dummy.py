# coding: utf-8
import logging
from ppyt.commands import CommandBase

logger = logging.getLogger(__name__)
plogger = logging.getLogger('print')


class Command(CommandBase):
    """特に意味のないコマンドです。"""

    def _add_options(self, parser):
        """コマンド実行時の引数を定義します。"""
        parser.add_argument('args', nargs='*')

    def _execute(self, options):
        logger.debug(self._command)
        logger.info('args: {}'.format(options.args))
        print('Hello World!')
