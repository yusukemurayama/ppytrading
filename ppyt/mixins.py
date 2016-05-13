# coding: utf-8
import logging

logger = logging.getLogger(__name__)


class FinderMixin(object):
    """SimpleFinderクラスで検索できるようにするためのMixinです。"""

    # 検索の際に使うキー
    _findkey = '継承したクラスで定義してください。'

    @classmethod
    def get_key(self):
        """キーを取得します。"""
        return self._findkey


class SingletonMixin(object):
    """継承したクラスをシングルトンするMixinです。"""

    __instance = None

    def __new__(cls):
        raise Exception('{classname}()でインスタンスを生成できません。'
                        '代わりに{classname}.getinstance()を使ってください。'
                        .format(classname=cls.__name__))

    @classmethod
    def getinstance(cls):
        """シングルトンなインスタンスを取得します。"""
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance


class ArgumentValidationMixin(object):
    """引数チェック用のMixinです。"""

    def _is_valid_argument(self, name, value, *types):
        """引数をチェックします。

        Args:
            name: 引数名
            value: 引数の値
            types: 引数の型

        Returns:
            True: 引数が正常な場合

        Raises:
            ArgumentError: 引数がNoneか、型が不正な場合
        """
        from ppyt.exceptions import ArgumentError
        if value is None or not isinstance(value, types):
            raise ArgumentError(name=name, strtype=', '.join([t.__name__ for t in types]))
        return True
