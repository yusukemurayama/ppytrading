# coding: utf-8
import logging
import time
import os
import abc
import json
import re
from datetime import date
import numpy as np
from ppyt import const
from ppyt.exceptions import CommandError, NewInstanceError, ArgumentError
from ppyt.finders import SimpleFinder
from ppyt.models.orm import Setting

logger = logging.getLogger(__name__)
plogger = logging.getLogger('print')


class CommandBase(metaclass=abc.ABCMeta):
    """各種コマンドの規定クラスです。"""

    def __init__(self, manager, command, args):
        """コンストラクタ

        Args:
            manager: managerスクリプトのファイル名
            command: 実行するコマンド名
            args: 引数のlist（コマンド名は除外されています。）
        """
        self._manager = manager
        self._command = command
        self._args = args

    @abc.abstractmethod
    def _add_options(self, parser):
        """argparseのルールを記述します。サブクラスでオーバーライドします。"""
        pass

    @abc.abstractmethod
    def _execute(self, options):
        """コマンドの本体です。サブクラスでオーバーライドします。"""
        pass

    def start(self):
        start_time = time.time()

        # 引数を解析します。
        import sys
        import argparse
        parser = argparse.ArgumentParser(prog='{} {}'.format(sys.argv[0], self._command))
        parser.add_argument('-v', '--verbose', action='store_true', default=False)
        self._add_options(parser)
        options = parser.parse_args(self._args)

        self._yyyymmdd = date.today().strftime('%Y%m%d')
        self._set_logger(options.verbose)
        np.seterr(invalid='ignore')

        try:
            logger.info('{}コマンドを開始します。'.format(self._command))
            self._execute(options)  # コマンドを実行します。
            logger.info('{}コマンドが正常に終了しました。実行時間: {}秒'.format(
                self._command, round(time.time()-start_time, 2)))

        except CommandError as e:
            # コマンド実行中に（軽微な）例外が発生したら画面に表示します。
            plogger.info(e)

        except Exception as e:
            # コマンド実行中に例外が発生したらログに出力し、呼び出し元に投げます。
            logger.error('{}コマンドが異常終了しました。原因: {}'.format(self._command, e))
            raise e

    def _set_logger(self, verbose):
        """ログ周りの設定をします。

        Arguments:
            verbose: Trueにすると詳細表示モードになります。
        """
        logger = logging.getLogger('')  # Root Logger
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(filename)s.%(funcName)s#%(lineno)s '
                                      '- %(levelname)s - %(message)s')

        # コンソール
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        del handler

        # ファイル
        handler = logging.FileHandler(os.path.join(
            const.LOG_DIR, '{}-command.log'.format(self._yyyymmdd)))
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        del handler

        # SQLAlchemyのログレベルを変更します。
        logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG if verbose else logging.WARN)

        # メッセージ表示用のロガーを準備します。
        plogger = logging.getLogger('print')
        plogger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        ch.setFormatter(formatter)
        plogger.addHandler(ch)
        plogger.propagate = False

    def _get_rulefilepath(self, rulefile):
        """ルールファイルのパスを取得します。

        Args:
            rulefile: 取得対象のルールファイル名

        Returns:
            ルールファイルのパス
        """
        return os.path.join(const.RULEFILE_DIR, rulefile + '.json')

    def _parse_rule(self, data, entry_rules=True):
        """ルール情報を解析して取得します。

        Args:
            data: 解析対象のルール情報を含むdict型オブジェクト
            entry_rules: Trueの場合はentry_rules、Falseの場合はexit_rulesとして扱います。

        Returns:
            解析したルールの情報を含むdict型オブジェクト
        """
        new_data = {}

        # 有効 / 無効を設定します。
        new_data['enabled'] = data.get('enabled', True)

        # order_typeを設定します。
        if data['order_type'].upper() == const.RULEFILE_ORDER_TYPE_LONG:
            order_type = const.ORDER_TYPE_LONG
        elif data['order_type'].upper() == const.RULEFILE_ORDER_TYPE_SHORT:
            order_type = const.ORDER_TYPE_SHORT
        else:
            raise CommandError('ルールファイルのorder_typeの指定に誤りがあります。'
                               'order_typeは[{} / {}]の中から指定してください。'
                               .format(const.RULEFILE_ORDER_TYPE_LONG,
                                       const.RULEFILE_ORDER_TYPE_SHORT))

        new_data['order_type'] = order_type

        # conditionsをインスタンス化して設定します。
        new_data['conditions'] = [self._newinstance(cond, const.RULE_TYPE_CONDITIONS)
                                  for cond in data.get('conditions') or []]

        # ruleをインスタンス化して設定します。
        if 'rule' not in data:
            raise CommandError('ルールファイルのentry_groupにruleが登録されていません。')

        if entry_rules:
            new_data['rule'] = self._newinstance(data['rule'], const.RULE_TYPE_ENTRYRULES)
        else:
            new_data['rule'] = self._newinstance(data['rule'], const.RULE_TYPE_EXITRULES)

        return new_data

    def _newinstance(self, data, rule_type):
        """ルール系のインスタンスを取得します。

        Args:
            data: 生成するインスタンスの情報を含むdict型オブジェクト
            rule_type: 生成するインスタンスの種類

        Returns:
            ルール系のインスタンス
        """
        kwds = data.copy()
        del data
        findkey = kwds.pop('findkey')

        if 'timing' in kwds:
            timing = str(kwds.pop('timing')).upper()
            if timing in const.RULEFILE_ORDER_TIMING_MAP.keys():
                kwds['timing'] = const.RULEFILE_ORDER_TIMING_MAP[timing]
            else:
                raise CommandError('ルールファイルのtimingの指定に誤りがあります。'
                                   'timingは[{}]の中から選んでください。'
                                   .format(' / '.join(const.RULEFILE_ORDER_TIMING_MAP.keys())))

        klass = SimpleFinder.getinstance().find_class(rule_type, findkey)

        if klass is None:
            msg = '[{}]のfindkey: [{}]に対応するクラスが見つかりませんでした。'.format(rule_type, findkey)
            raise NewInstanceError(msg=msg)

        self.__update_kwds(kwds)
        logger.debug('kwds: {}'.format(kwds))
        try:
            obj = klass(**kwds)
        except ArgumentError as err:
            raise NewInstanceError(msg='{}'.format(err), rule_type=rule_type, findkey=findkey)
        except Exception as err:
            raise NewInstanceError(rule_type=rule_type, findkey=findkey, err=err)
        return obj

    def _get_default_rulefile(self):
        """デフォルトのrulefileを取得します。"""
        return Setting.get_value(Setting.KEY_DEFAULTRULEFILE) or 'default'

    def _get_rules(self, rulefile):
        """ルールファイルを解析し、生成したインスタンスを取得します。

        Args:
            rulefile: 取得対象のルールファイル

        Returns:
            entry_groupsとexit_groupsが入ったdict型オブジェクト
        """
        filepath = self._get_rulefilepath(rulefile)

        if not os.path.isfile(filepath):
            msg = 'ルールファイル[{}]が見つかりませんでした。'.format(filepath)
            raise CommandError(msg)

        with open(filepath, encoding=const.DEFAULT_FILE_ENCODING) as fp:
            data = json.load(fp)

        logger.debug('data: {}'.format(data))

        # enabledがTrueになっているentry_groupのリストを取得します。
        entry_groups = [eg for eg in [self._parse_rule(rule, True) for rule in data['entry_groups']]
                        if eg['enabled']]

        # enabledがTrueになっているexit_groupのリストを取得します。
        exit_groups = [eg for eg in [self._parse_rule(rule, False) for rule in data['exit_groups']]
                       if eg['enabled']]

        if not entry_groups or not exit_groups:
            raise CommandError('entry_groupsかexit_groupが見つかりませんでした。'
                               'ルールファイルを見なおしてください。')

        return {'entry_groups': entry_groups,
                'exit_groups': exit_groups}

    def _get_default_filterfile(self):
        """デフォルトのfilterfileを取得します。"""
        return Setting.get_value(Setting.KEY_DEFAULTFILTERFILE) or 'default'

    def _get_stock_filters(self, filterfile):
        """filterfileを解析してfilter系クラスのインスタンスを取得します。

        Args:
            filterfile: 取得対象のフィルタ情報が記述されたファイル

        Returns:
            フィルタクラスのインスタンスのリスト
        """
        filters = []
        filepath = os.path.join(const.FILTERFILE_DIR, filterfile + '.json')
        logger.debug('rule filepath: {}'.format(filepath))

        if not os.path.isfile(filepath):
            msg = 'フィルタファイル[{}]が見つかりませんでした。'.format(filepath)
            raise CommandError(msg)

        with open(filepath, encoding=const.DEFAULT_FILE_ENCODING) as fp:
            data = json.load(fp)

        logger.debug('data: {}'.format(data))

        for filter_data in data['filters']:
            filters.append(self._newinstance(filter_data, const.RULE_TYPE_FILTERS))

        return filters

    def _prepare_directory(self, dirpath):
        """ディレクトリを作成します。
        Args:
            dirpath: ディレクトリ作成場所

        Returns:
            ディレクトリを作成した場合はTrue、既にディレクトリがある場合はFalseを返します。

        Raises:
            CommandError: ディレクトリ作成場所に、既にファイルが存在する場合に発生します。
        """
        if os.path.isdir(dirpath):
            return False  # ディレクトリが既にある場合は何もせずに戻ります。

        if os.path.isfile(dirpath):
            # ディレクトリを作成する場所にファイルがある場合は、例外を投げます。
            raise CommandError('ディレクトリ[{}]を作成できませんでした。'
                               '既にファイルが存在します。'.format(dirpath))

        os.makedirs(dirpath)  # ディレクトリを作成します。
        return True

    def _show_classes(self, rule_type):
        """指定したrule_typeのクラスを一覧表示します。"""
        import string
        plogger.info(os.linesep + '# {}のfindkey一覧'.format(string.capwords(rule_type)))
        for findkey in sorted(SimpleFinder.getinstance().find_class_all(rule_type).keys()):
            plogger.info('- ' + findkey)

    def _show_indicators(self):
        """indicatorの一覧を表示します。"""
        return self._show_classes(const.RULE_TYPE_INDICATORS)

    def _show_conditions(self):
        """conditionの一覧を表示します。"""
        return self._show_classes(const.RULE_TYPE_CONDITIONS)

    def _show_entry_rules(self):
        """entry_ruleの一覧を表示します。"""
        return self._show_classes(const.RULE_TYPE_ENTRYRULES)

    def _show_exit_rules(self):
        """exit_ruleの一覧を表示します。"""
        return self._show_classes(const.RULE_TYPE_EXITRULES)

    def _show_filters(self):
        """filterの一覧を表示します。"""
        return self._show_classes(const.RULE_TYPE_FILTERS)

    def _eqlist_to_dict(self, args):
        """=で句切られた文字列が入ったリストから、dict型に変換して取得します。
        Args:
            args: =で句切られた文字列を含んだリスト

        Returns:
            dict型オブジェクト
            例: foo=FOO bar=BAR -> {'foo': 'FOO', 'bar': 'BAR'}
        """
        if args is None:
            return {}

        li = []
        for kv in args:
            if kv.count('=') != 1:
                continue
            k, v = kv.split('=')
            li.append((k, v))
        kwds = {k: v for k, v in li}
        self.__update_kwds(kwds)
        return kwds

    def _prepare_data_directories(self):
        """入力データを置くディレクトリを作成します。"""
        for dirpath in (const.DATA_DIR, ) + const.DATA_SUB_DIRS:
            if self._prepare_directory(dirpath):
                plogger.info('ディレクトリ[{}]を作成しました。'.format(
                    os.path.relpath(dirpath, start=const.PRJ_DIR)))

    def _iter_rows_from_csvfile(self, filepath, encoding=None, as_dict=False):
        """CSVファイルを読み込んで行を取得します。

        Args:
            filepath: CSVファイルのパス
            encoding: 読み込むCSVファイルのエンコーディング
            as_dict: listではなくdict型で返します。

        Raises:
            Exception: 拡張子が.csvでない場合に発生します。※拡張子のみで、中身はチェックしません。
        """
        import csv
        if not re.search(r'\.csv$', filepath, re.I):
            raise Exception('ファイル[{}]の拡張子が.csvではありません。'
                            .format(os.path.basename(filepath)))
        encoding = encoding or const.DEFAULT_FILE_ENCODING
        with open(filepath, encoding=encoding) as fp:
            text = fp.read()
            text = re.sub(r'(?:\r\n|\r)', '\n', text)
        # 改行コードの違いによって空行があった場合は飛ばします。
        reader = csv.reader([row for row in text.splitlines(False) if row.strip() != ''])
        del text

        headers = next(reader)

        for row in reader:
            if not as_dict:
                yield row
            else:
                # dict型として返します。
                yield {header_name: row[i] for (i, header_name) in enumerate(headers)}

    def _move_to_done_dir(self, filepath):
        """ファイルを完了済みディレクトリに移動します。

        Args:
            filepath: 移動するファイル
        """
        # 出力先を決定します。
        # 例:
        #   FROM: /path/to/data/history/foo.csv
        #   TO:   /path/to/data/done/20161229/history/foo.csv
        dest_path = os.path.join(const.DATA_DIR,
                                 'done',
                                 self._yyyymmdd,
                                 os.path.relpath(filepath, const.DATA_DIR))
        logger.debug('dest_path: %s' % dest_path)

        # ファイルを移動します。
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        os.rename(filepath, dest_path)

    def __update_kwds(self, kwds):
        """引数で与えられたdict型オブジェクトに含まれる、
        int型やfloat型に変換できる値を変換します。"""
        for k, v in kwds.items():
            if type(v) != str:
                continue
            if re.search(r'^-?[0-9]+$', v):
                v = int(v)
            elif re.search(r'^-?[1-9][0-9]*\.[0-9]+$', v):
                v = float(v)
            kwds[k] = v
