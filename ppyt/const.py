# coding: utf-8
import os

# ディレクトリ関連を定義します。
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PRJ_DIR = os.path.dirname(BASE_DIR)
RULEFILE_DIR = os.path.join(PRJ_DIR, 'rules')  # ruleファイルの置き場所
FILTERFILE_DIR = os.path.join(PRJ_DIR, 'filters')  # filterファイルの置き場所
DATA_DIR = os.path.join(PRJ_DIR, 'data')
DATA_DIR_STOCKLIST = os.path.join(DATA_DIR, 'stock_list')
DATA_DIR_FINANCIAL = os.path.join(DATA_DIR, 'financial_data')
DATA_DIR_HISTORY = os.path.join(DATA_DIR, 'history')
DATA_SUB_DIRS = (
    DATA_DIR_STOCKLIST,
    DATA_DIR_FINANCIAL,
    DATA_DIR_HISTORY,
)
OUTPUT_DIR = os.path.join(PRJ_DIR, 'output')
OUTPUT_BACKTEST_DIR = os.path.join(OUTPUT_DIR, 'backtest')
OUTPUT_INDICATOR_DIR = os.path.join(OUTPUT_DIR, 'indicators')

# DB接続情報
DSN = 'sqlite:///{}'.format(
    os.path.join(PRJ_DIR, 'db.sqlite3')
)

# Logファイルのパスです。
LOG_DIR = os.path.join(PRJ_DIR, 'logs')

# 集計結果を計算できない場合に表示する文字です。
# 0で除算するのを回避したときなどに使います。
NAN = 'NaN'

# マーケット関連の値を定義します。
MARKET_DATA = {
    1: 'nyse',
    2: 'nasdaq',
}

# 金額に関する値を定義をします。
PRICE_TYPE_OPEN = 'open_price'
PRICE_TYPE_HIGH = 'high_price'
PRICE_TYPE_LOW = 'low_price'
PRICE_TYPE_CLOSE = 'close_price'

# 売買に関する値を定義します。
ORDER_TYPE_LONG = 1  # 買い
ORDER_TYPE_SHORT = 2  # 売り
ORDER_TYPES = (
    ORDER_TYPE_LONG,
    ORDER_TYPE_SHORT,
)

# 注文時間に関する定義します。
ORDER_TIMING_OPEN = 1  # 寄付
ORDER_TIMING_SESSION = 2  # ザラ場中
ORDER_TIMING_CLOSE = 3  # 引け
ORDER_TIMING_ANYTIME = 4  # いつでも
ORDER_TIMING_DATA = {
    ORDER_TIMING_OPEN: '寄付',
    ORDER_TIMING_SESSION: 'ザラ場',
    ORDER_TIMING_CLOSE: '引け',
}
ORDER_TIMINGS = tuple(ORDER_TIMING_DATA.keys())

# 呼値の上昇・下降の最小単位
MIN_PRICE_UPDOWN = 0.01

# 指標期間（25日移動平均線の場合は25が期間）の最大値を定義します。
MAX_SPAN = 365

# CSVファイルのエンコーディングのデフォルトを定義します。
DEFAULT_FILE_ENCODING = 'utf-8'

# 1回の仕掛けに使う資金量のデフォルトを定義します。
DEFAULT_AMOUNT_PER_TRADE = 5000

# indicatorをキャッシュする最大数
MAX_INDICATOR_CACHES = 1000

# ルールの種別
RULE_TYPE_INDICATORS = 'indicators'
RULE_TYPE_CONDITIONS = 'conditions'
RULE_TYPE_ENTRYRULES = 'entry_rules'
RULE_TYPE_EXITRULES = 'exit_rules'
RULE_TYPE_FILTERS = 'filters'

# ルールファイル関連の値を定義します。: START
RULEFILE_ORDER_TYPE_LONG = 'LONG'
RULEFILE_ORDER_TYPE_SHORT = 'SHORT'

RULEFILE_ORDER_TIMING_OPEN = 'OPEN'
RULEFILE_ORDER_TIMING_SESSION = 'SESSION'
RULEFILE_ORDER_TIMING_CLOSE = 'CLOSE'
RULEFILE_ORDER_TIMING_ANYTIME = 'ANYTIME'
RULEFILE_ORDER_TIMING_MAP = {
    RULEFILE_ORDER_TIMING_OPEN: ORDER_TIMING_OPEN,
    RULEFILE_ORDER_TIMING_SESSION: ORDER_TIMING_SESSION,
    RULEFILE_ORDER_TIMING_CLOSE: ORDER_TIMING_CLOSE,
    RULEFILE_ORDER_TIMING_ANYTIME: ORDER_TIMING_ANYTIME,
}
# ルールファイル関連の値を定義します。: END

# 指標の方向関連
INDI_DIRECTION_UP = 1  # 上昇
INDI_DIRECTION_DOWN = -1  # 下降
INDI_DIRECTION_HR = 0  # 水平
