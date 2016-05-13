# coding: utf-8
import logging
from functools import wraps
from ppyt.exceptions import NoDataError

logger = logging.getLogger(__name__)


def handle_nodataerror(nodata_return):
    """NoDataErrorを処理するデコレータです。
    このデコレータをつけておくと、内部でNoDataErrorが発生したときに[nodata_return]が返るようになります。

    Args:
        nodata_return: NoDataError発生時に返る値

    Retusn:
        関数・メソッドの実行結果
        ※関数・メソッドでNoDataErrorが発生したら、nodata_returnが返ります。
    """

    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwds):
            try:
                return func(*args, **kwds)
            except NoDataError:
                # NoDataErrorが投げられたらnodata_returnを返します。
                return nodata_return
        return inner
    return wrapper


class cached_property(object):
    """プロパティの値をキャッシュします。それにより、2回目以降のアクセス時の負荷を下げます。
    評価されたプロパティの結果は、そのプロパティが定義されているインスタンス自身に格納されます。"""

    def __init__(self, func):
        """コンストラクタ

        Args:
            func: cache_propertyでデコレートされたメソッド
                ※cached_propertyをつけたときは、プロパティのように
                ()なしでメソッドが走るようになります。
        """
        self._func = func

    def __get__(self, obj, klass):
        # プロパティが定義されているインスタンス自身から、cache_keyを使って辞書型の属性を取得します。
        cache_key = '__CACHED_PROPERTY_DICT'  # キャッシュデータ用のインスタンス変数名
        cache = getattr(obj, cache_key, None)
        if cache is None:
            # まだ辞書型の属性がない場合は、インスタンスに追加しておきます。
            cache = {}
            setattr(obj, cache_key, cache)

        propname = self._func.__name__  # プロパティの名前を取得します。
        if propname not in cache:
            # キャッシュされていない場合はメソッドを実行し、その結果をキャッシュします。
            cache[propname] = self._func(obj)
            logger.debug('propname[{}]をキャッシュしました。'.format(propname))

        else:
            # キャッシュにヒットしたことをログに書き込んでおきます。
            logger.debug('propname[{}]をキャッシュから取得します。'.format(propname))

        return cache[propname]
