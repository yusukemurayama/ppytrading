# coding: utf-8
import logging
import abc
import numpy as np
from ppyt import const
from ppyt.mixins import FinderMixin, SingletonMixin
from ppyt.exceptions import CommandError

logger = logging.getLogger(__name__)


class IndicatorBase(FinderMixin, metaclass=abc.ABCMeta):
    """indicatorの基底クラスです。"""

    def __init__(self, stock, span=None, **kwds):
        """コンストラクタ

        Args:
            stock: 銘柄情報
            span: 集計期間（XX日移動平均線などのXX日）
        """
        self.stock = stock
        self.__span = span
        self.__kwds = kwds
        self.__data = None

    @abc.abstractmethod
    def _build_indicator(self, *args, **kwds):
        """indicatorのデータを構築します。サブクラスで実装してください。

        Returns:
            indicatorのデータ（numpyの配列）
        """
        pass

    @property
    def name_with_args(self):
        """名前と（生成時の）引数を連結した文字列を取得します。

        Returns:
            クラス名 - foo=FOO bar=BAR
        """
        strargs = ''
        if self.__span is not None:
            strargs += ' span={}'.format(self.__span)

        for k, v in self.__kwds.items():
            strargs += ' {}={}'.format(k, v)
        return '{} - {}'.format(self.get_key(), strargs)

    @property
    def data(self):
        """indicatorのデータ（numpyの配列）を取得します。"""
        if self.__data is None:
            self.build()  # dataがまだない場合は構築します。
        return self.__data

    def build(self):
        """indicatorのデータを構築します。"""
        instance = IndicatorCache.getinstance()
        data = instance.get_data(klass=self.__class__, stock=self.stock,
                                 span=self.__span, **self.__kwds)
        if data is None:
            # indicatorを組み立てます。
            data = self._build_indicator(span=self.__span, **self.__kwds)
            instance.add_data(data=data,
                              klass=self.__class__,
                              stock=self.stock,
                              span=self.__span,
                              **self.__kwds)
        self.__data = data

    def get(self, idx):
        """indicatorのデータを1日分取得します。

        Args:
            idx: 日々のデータにアクセスするための添字

        Returns:
            1日分のindicatorデータ
        """
        from ppyt.exceptions import NoDataError
        if idx < 0 or idx >= len(self.data):
            raise NoDataError()
        val = self.data[idx]
        if np.isnan(val):
            raise NoDataError()  # numpy.nanは例外を投げます。
        return val

    def spanned_data(self, price_type=const.PRICE_TYPE_CLOSE):
        """span日分のデータを集めたリストを取得します。
            例:
                [10, 20, 30, 40, 50]でspanが2
                ↓
                [
                    [NaN, NaN], [10, 20], [20, 30], [30, 40], [40, 50],
                ]

        Args:
            price_type: 参照する値段の種別（
                open_price, high_price, low_price, close_price）

        Returns:
            新しく生成したnumpyの配列
        """
        if self.__span is None:
            raise CommandError('spanが指定されていません。')

        if self.__span > const.MAX_SPAN:
            raise CommandError('指定されたspan[{}]が最大値[{}]を超えています。'
                               .format(self.__span, const.MAX_SPAN))

        data = [getattr(hist, price_type) for hist in self.stock.histories]

        if len(data) < self.__span:
            # データが不足していて指標作成不能な場合はすべてnanで埋めた、
            # shapeが(時系列データ数, 期間)の配列を返します。
            s_nan_arr = np.empty((len(data), self.__span), dtype=np.float64)
            s_nan_arr.fill(np.nan)
            return s_nan_arr

        # nanで埋める分の配列を用意します。
        nan_arr = np.empty((self.__span-1, self.__span), dtype=np.float64)
        nan_arr.fill(np.nan)

        # データが入る配列を作成します。
        data_arr = np.array([data[i: i + self.__span]
                             for i in range(len(
                                     self.stock.histories) - self.__span + 1)],
                            dtype=np.float64)
        spanned_data = np.concatenate((nan_arr, data_arr), axis=0)
        logger.debug('spanned_data: {}'.format(spanned_data))

        return spanned_data

    def shifted(self, num):
        """左、または右方向にnum分ずらした配列を取得します。
        ※ずらしても配列のサイズは変更されません。新しく出現した場所にはNaNが入っています。

        Args:
            num: ずらす数（マイナスだと左、プラスだと右にずらす）

        Returns:
            num分ずらした配列
        """
        if num == 0 or len(self.data.shape) > 2:
            raise CommandError('[{}]の配列を操作できませんでした。shiftedメソッドは'
                               'NxNの配列までにしか対応していません。'.format(self.data.shape))

        if num < 0:
            pad_width = (abs(num), 0)
        elif num > 0:
            pad_width = (0, num)

        if len(self.data.shape) == 2:
            pad_width = (pad_width, (0, 0))

        return np.lib.pad(self.data, pad_width, 'constant',
                          constant_values=(np.nan))[0:len(self.data)]


class IndicatorCache(SingletonMixin):
    """※マルチスレッドでの処理を考慮していないので、
    スレッドセーフを実現していません。
    """
    __cache = {}
    __keys = []

    def get_key(self, klass, stock, **kwds):
        """キャッシュするときのキーを取得します。

        Args:
            klass: IndicatorBaseを継承したクラスオブジェクト
            stock: 銘柄情報

        Returns:
            キャッシュを一意に特定できるキー
        """
        def is_valid_kwvalue(v):
            return v is None or type(v) in (bool, str, int, float)

        if stock is None or stock.symbol is None:
            return None

        if any([not is_valid_kwvalue(v) for v in kwds.values()]):
            return None

        return '{}-symbol:{}-{}'.format(klass.__name__, stock.symbol,
                                        '-'.join(['{}:{}'.format(k, v)
                                                  for k, v in kwds.items()]))

    def get_data(self, klass, stock, **kwds):
        """キャッシュからindicatorのデータを取得します。ヒットしない場合はNoneが返ります。

        Args:
            klass: IndicatorBaseを継承したクラスオブジェクト
            stock: 銘柄情報

        Returns:
            キャッシュされていたindicatorのdata
        """
        key = self.get_key(klass, stock, **kwds)
        logger.debug('key: {}'.format(key))

        if key is None or key not in self.__cache:
            logger.debug('key[{}]はキャッシュされていませんでした。'.format(key))
            return None

        logger.debug('key[{}]をキャッシュから取得します。'.format(key))
        return self.__cache[key]

    def add_data(self, data, klass, stock, **kwds):
        """indicatorのデータをキャッシュします。

        Args:
            data: キャッシュするデータ
            klass: IndicatorBaseを継承したクラスオブジェクト
            stock: 銘柄情報
        """
        from ppyt.const import MAX_INDICATOR_CACHES as MAX_CACHES
        if MAX_CACHES == 0:
            logger.debug('キャッシュは無効になっています。')
            return

        key = self.get_key(klass, stock, **kwds)

        if key is None:
            return

        if key not in self.__cache and len(self.__keys) >= MAX_CACHES:
            del_key = self.__keys.pop(0)
            logger.debug('キャッシュが一杯なので、key[{}]で登録されたキャッシュを削除します。'
                         .format(del_key))
            del self.__cache[del_key]

        self.__cache[key] = data
        logger.debug('key[{}]をキャッシュしました。'.format(key))
        self.__keys.append(key)  # キーを登録しておきます。


class IndicatorTemplate(IndicatorBase):
    """indicatorクラスのテンプレートです。"""

    _findkey = 'テンプレート'  # indicatorを一意に特定できる名前をつけます。

    def _build_indicator(self, **kwds):
        """indicatorのデータを組み立てます。

        Args:
            引数1:
            ...

        Returns:
            indicatorのデータ（numpyの配列）
        """
        pass
