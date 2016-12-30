# coding: utf-8
import logging
import os
from ppyt import const
from ppyt.commands import CommandBase
from ppyt.models.orm import Setting

logger = logging.getLogger(__name__)
plogger = logging.getLogger('print')


class Command(CommandBase):
    """Settingを更新を行います。"""

    def _add_options(self, parser):
        # 指定すると現在の登録内容を確認できます。
        parser.add_argument('-l', '--list', action='store_true')

    def _execute(self, options):
        if options.list is True:
            plogger.info(os.linesep + '# Setting一覧' + os.linesep)
            for row in Setting.get_list():
                plogger.info('- Key: {}, Value: {}'.format(row.key, row.value))
            plogger.info(os.linesep)

        else:
            selected_key = self.__select_key()
            selected_value = self.__select_value(selected_key)
            logger.debug('selected_value: %s' % selected_value)

            # Settingを更新します。
            Setting.save(selected_key, selected_value)
            plogger.info('Key [%s] の値を [%s]に更新しました。' % (selected_key, selected_value))

    def __select_key(self):
        """Key選択を表示して、入力を受け取ります。"""
        plogger.info('以下の中から更新するKeyを数字で選択してください。' + os.linesep)
        key_map = {(i + 1): k for i, k in enumerate(Setting.get_keys())}
        return self.__get_number(key_map)

    def __select_value(self, key):
        """value選択を表示し、入力を受け取ります。"""
        current_value = Setting.get_value(key)
        plogger.info('以下の中から更新内容を数字で選択してください。' + os.linesep)

        if key == Setting.KEY_DEFAULTRULEFILE:
            values = sorted([os.path.splitext(fn)[0] for fn in os.listdir(const.RULEFILE_DIR)
                             if os.path.splitext(fn)[1].lower() == '.json'])

        elif key == Setting.KEY_DEFAULTFILTERFILE:  # フィルタファイル
            values = sorted([os.path.splitext(fn)[0] for fn in os.listdir(const.FILTERFILE_DIR)
                             if os.path.splitext(fn)[1].lower() == '.json'])

        # key: （選択可能な数字）, value: 設定値のdict型変数を定義します。
        value_map = {}

        if current_value in values:  # 設定可能な値の中に、現在の設定値がある場合
            values.remove(current_value)  # 一覧から削除します。
            value_map[0] = current_value  # 0番として現在値を追加します。

        # key: 1以降のkeyを追加していきます。
        value_map.update({(i + 1): v for i, v in enumerate(values)})

        return self.__get_number(value_map)

    def __get_number(self, selectable_map):
        """入力を受け付け、入力された内容を取得します。"""
        str_numbers = [str(v) for v in selectable_map.keys()]

        # 選択可能な値を表示します。
        plogger.info(os.linesep.join(['- {}: {} {}'.format(i, v, '（現在値）' if i == 0 else '')
                                      for i, v in selectable_map.items()]) + os.linesep)

        if len(str_numbers) == 0:
            from ppyt.exceptions import CommandError
            raise CommandError('選択可能な値がありません。')

        # 入力を待ちます。
        while True:
            msg_prefix = '{}-{}'.format(str_numbers[0], str_numbers[-1]) \
                if len(str_numbers) > 1 else '{}'.format(str_numbers[0])
            str_number = input('[{}]の数字を入力してください。: '.format(msg_prefix))

            if str_number in str_numbers:
                break

        return selectable_map[int(str_number)]
