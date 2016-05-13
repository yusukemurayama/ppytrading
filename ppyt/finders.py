# coding: utf-8
import logging
import os
import importlib
import inspect
from ppyt import const
from ppyt.mixins import SingletonMixin
from ppyt.exceptions import DuplicateFindkeyError

logger = logging.getLogger(__name__)


class SimpleFinder(SingletonMixin):
    """indicatorsなどを検索するクラスです。
    検索対象とするクラスはppyt.mixins.FinderMixinを継承させておく必要があります。"""

    __class_map = {  # 取得済みクラスを格納しておく辞書型のクラス変数
        const.RULE_TYPE_INDICATORS: None,
        const.RULE_TYPE_CONDITIONS: None,
        const.RULE_TYPE_ENTRYRULES: None,
        const.RULE_TYPE_EXITRULES: None,
        const.RULE_TYPE_FILTERS: None,
    }

    def find_class(self, rule_type, findkey):
        """rule_typeとfindkeyを指定してクラスオブジェクトを取得します。

        Args:
            rule_type: 取得するクラスの種別 （__class_map.keys()を指定可能）
            findkey: クラスを一意に特定するキー

        Returns:
            クラスオブジェクト
        """
        if self.__class_map[rule_type] is None:
            # 指定されたrule_typeがまだロードされていない場合はロードします。
            self.__load_classes(rule_type)
        return self.__class_map[rule_type].get(findkey, None)

    def find_class_all(self, rule_type):
        """指定したrule_typeに含まれるクラスをすべて取得します。

        Args:
            rule_type: 取得するクラスの種別 （__class_map.keys()を指定可能）

        Returns:
            クラスオブジェクトのリスト
        """
        if self.__class_map[rule_type] is None:
            # 指定されたrule_typeがまだロードされていない場合はロードします。
            self.__load_classes(rule_type)
        return self.__class_map[rule_type]

    def __iter_classes(self, dirpath, baseclass):
        """引数で指定したディレクトリに含まれる、特定のクラスを継承したクラスを取得します。

        Args:
            dirpath: 取得対象のディレクトリ
            baseclass: 取得対象のクラスの継承元となるクラス

        Yields:
            クラスオブジェクト
        """
        logger.debug('dirpath: {}'.format(dirpath))
        for filepath in self.__iter_pyfiles(dirpath):
            root, ext = os.path.splitext(filepath)
            module = importlib.import_module(root.replace(os.sep, '.'))
            for name, obj in inspect.getmembers(module):  # モジュールのメンバーを取得
                if not inspect.isclass(obj):
                    continue  # class以外は飛ばします。
                if not issubclass(obj, baseclass):
                    continue  # baseclassのサブクラスでない場合は飛ばします。
                if name == baseclass.__name__:
                    continue  # baseclass自体は飛ばします。
                if module.__name__ != obj.__module__:
                    continue  # 自分が定義していないクラスは飛ばします。
                yield obj

    def __iter_pyfiles(self, dirpath):
        """引数で指定したディレクトリに含まれる、拡張子がpyのファイルを返します。

        Args:
            dirpath: 取得対象のディレクトリ

        Yields:
            ファイルパス
        """
        for (dirpath, dirnames, filenames) in os.walk(dirpath):
            for fn in filenames:
                relpath = os.path.relpath(dirpath)
                if fn.endswith('.py'):
                    yield os.path.join(relpath, fn)

    def __load_classes(self, rule_type):
        """クラスを取得して__class_mapに追加します。

        Args:
            rule_type: 取得するクラスの種別 （__class_map.keys()を指定可能）
        """
        from ppyt.indicators import IndicatorBase
        from ppyt.filters import FilterBase
        from ppyt.rules.conditions import ConditionBase
        from ppyt.rules.entry_rules import EntryBase
        from ppyt.rules.exit_rules import ExitBase
        data = {}

        # rule_typeを見てdirpathとbaseclassを決定します。
        if rule_type == const.RULE_TYPE_INDICATORS:
            dirpath = os.path.join(const.BASE_DIR, 'indicators')
            baseclass = IndicatorBase
        elif rule_type == const.RULE_TYPE_CONDITIONS:
            dirpath = os.path.join(const.BASE_DIR, 'rules', 'conditions')
            baseclass = ConditionBase
        elif rule_type == const.RULE_TYPE_ENTRYRULES:
            dirpath = os.path.join(const.BASE_DIR, 'rules', 'entry_rules')
            baseclass = EntryBase
        elif rule_type == const.RULE_TYPE_EXITRULES:
            dirpath = os.path.join(const.BASE_DIR, 'rules', 'exit_rules')
            baseclass = ExitBase
        elif rule_type == const.RULE_TYPE_FILTERS:
            dirpath = os.path.join(const.BASE_DIR, 'filters')
            baseclass = FilterBase

        # dirpathの中にある、baseclassを継承したクラスを取得します。
        for klass in self.__iter_classes(dirpath, baseclass):
            findkey = klass.get_key()
            if findkey in data.keys():
                # キーが重複している場合は例外を投げます。
                raise DuplicateFindkeyError(rule_type, findkey)

            # キーとクラスオブジェクトのペアをdataに追加します。
            data[findkey] = klass
        self.__class_map[rule_type] = data  # クラス変数にセットしておきます。
