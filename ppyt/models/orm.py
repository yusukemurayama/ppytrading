# coding: utf-8
import logging
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, ForeignKey, Integer, String,
    Float, Date, DateTime, SmallInteger, Boolean, UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker, reconstructor
from ppyt import const
from ppyt.decorators import cached_property
from ppyt.utils import str_to_number

logger = logging.getLogger(__name__)
Base = declarative_base()
engine = create_engine(const.DSN, echo=False)
Session = sessionmaker(bind=engine, autocommit=False)
DEFINED_TABLE_CLASSES = {}


@contextmanager
def start_session(commit=False):
    """セッションを開始します。

    Args:
        commit: Trueにするとセッション終了時にcommitします。

    Yields:
        SqlAlcyemyのセッション

    Usage:
        with start_session() as session:
            q = session.query(Table)...
    """
    session = None
    try:
        # トランザクションを開始します。
        # ※autocommit=Falseなので、自動的にトランザクションが開始されます。
        session = Session()
        try:
            yield session
            if commit:
                session.commit()
        except:
            # 例外発生時はトランザクションをロールバックして、その例外をそのまま投げます。
            session.rollback()
            raise
    finally:
        if session is not None:
            session.close()


class Sector(Base):
    """セクターの情報を持つクラスです。"""

    __tablename__ = 'sector'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=True, unique=True)  # セクター名
    created_at = Column(DateTime, default=datetime.now())  # 作成日時
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())  # 更新日時

    @classmethod
    def get_or_create(cls, session, name):
        """nameに一致するセクターが登録済みの場合は取得します。
        ない場合は作成して返します。

        Args:
            session: SQLAlchemyのセッションオブジェクト
            name: セクターの名前
        """
        name = name.strip()
        q = session.query(cls).filter_by(name=name)

        if session.query(q.exists()).scalar():
            # レコードが既に存在する場合は取得して返します。
            return q.one(), False

        # 存在しない場合は作成して返します。
        sector = Sector()
        sector.name = name
        session.add(sector)
        return sector, True


# Sectorテーブルを作成します。
Base.metadata.create_all(engine, tables=[Sector.__table__], checkfirst=True)


class Stock(Base):
    """銘柄の情報を持つクラスです。"""

    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)  # 銘柄の名前
    symbol = Column(String(16), nullable=False, unique=True)  # 銘柄のシンボル
    market_id = Column(Integer, nullable=False)  # マーケットID
    sector_id = Column(Integer, ForeignKey('sector.id', ondelete='RESTRICT'),
                       index=True, nullable=False)  # セクターID
    activated = Column(Boolean, default=False)  # Trueだとbacktestなどの対象になります。
    created_at = Column(DateTime, default=datetime.now())  # 作成日時
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())  # 更新日時

    @reconstructor
    def initialize(self):
        """コンストラクタ"""
        self.start_date = None
        self.end_date = None

    @cached_property
    def histories(self):
        """履歴データ（日毎の価格や出来高などを）を取得します。
        ※このプロパティの結果はキャッシュされます。そのため、
        日付（start_date, end_date）を設定してから呼ぶようにしてください。

        Returns:
            ppyt.models.orm.HistoryBase（のサブクラス）のリスト
        """
        with start_session() as session:
            # 銘柄ごとに異なるHistoryBaseを継承したクラスを取得します。
            klass = HistoryBase.get_class(self)
            if klass is None:
                # クラスがない場合は空のリストを返します。
                return []

            query = session.query(klass)
            if self.start_date is not None:
                # start_dateが設定されている場合は絞り込み条件に追加します。
                query = query.filter(klass.date >= self.start_date)

            if self.end_date is not None:
                # end_dateが設定されている場合は絞り込み条件に追加します。
                query = query.filter(klass.date <= self.end_date)

            return query.order_by('date').all()

    @classmethod
    def save(cls, session, name, symbol, market_id, sector_name):
        """レコードを新規作成・更新します。"""
        name = name.strip()
        symbol = symbol.strip()
        sector_name = sector_name.strip()
        sector, created = Sector.get_or_create(session, sector_name)
        if created:
            logger.info('セクター[{}]が新規作成されませした。'.format(sector_name))

        q = session.query(cls).filter_by(symbol=symbol)

        if session.query(q.exists()).scalar():
            # レコードが既に存在する場合は取得して上書きします。
            create_flag = False
            stock = q.one()

        else:
            # レコードが存在しない場合は新規作成します。
            create_flag = True
            stock = cls()

        stock.name = name
        stock.symbol = symbol
        stock.market_id = market_id
        stock.sector_id = sector.id

        if create_flag:
            session.add(stock)

    def set_date(self, start_date, end_date):
        """historiesの絞り込みに使う開始日と終了日を設定します。

        Args:
            start_date: 開始日
            end_date: 終了日
        """
        self.start_date = start_date
        self.end_date = end_date

    def get_history(self, idx):
        """indexを指定した日の履歴情報を1件取得します。

        Args:
            idx: 日付を特定できるindex

        Returns:
            履歴情報（ppyt.models.orm.HistoryBaseのサブクラス）

        Raises:
            NoDataError: idxに対する履歴データが存在しない場合
        """
        from ppyt.exceptions import NoDataError
        if idx < 0 or idx >= len(self.histories):
            raise NoDataError()
        return self.histories[idx]

    def get_date(self, idx):
        """indexに対する日付を取得します。

        Args:
            idx: 日付を特定できるindex

        Returns:
            日付（datetime.dateクラスのオブジェクト）
        """
        return self.get_history(idx).date

    def get_price(self, idx, price_type=const.PRICE_TYPE_CLOSE):
        """indexで指定した日の価格情報を取得します。取得する価格の種類はprice_typeで決定します。

        Args:
            idx: 日付を特定できるindex
            price_type: 価格種別

        Returns:
            価格
        """
        return getattr(self.get_history(idx), price_type)

    def get_open_price(self, idx):
        """indexで指定した日の始値を取得します。"""
        return self.get_price(idx, price_type=const.PRICE_TYPE_OPEN)

    def get_high_price(self, idx):
        """indexで指定した日の高値を取得します。"""
        return self.get_price(idx, price_type=const.PRICE_TYPE_HIGH)

    def get_low_price(self, idx):
        """indexで指定した日の安値を取得します。"""
        return self.get_price(idx, price_type=const.PRICE_TYPE_LOW)

    def get_close_price(self, idx):
        """indexで指定した日の終値を取得します。"""
        return self.get_price(idx, price_type=const.PRICE_TYPE_CLOSE)

    def get_prices(self, price_type=const.PRICE_TYPE_CLOSE):
        """指定した価格種別のリストを取得します。

        Args:
            price_type: 価格種別

        Returns:
            価格のリスト
        """
        return [getattr(self.histories[idx], price_type) for idx in range(len(self.histories))]


# Stockテーブルを作成します。
Base.metadata.create_all(engine, tables=[Stock.__table__], checkfirst=True)


class HistoryBase(object):
    """履歴情報（日毎の始値、終値などを保存持つ）の親クラスです。
    各銘柄毎にHistoryBaseのサブクラスが作られ、それに応じて銘柄毎にテーブルが作成されます。"""

    date = Column(Date, primary_key=True)  # 日付
    raw_close_price = Column(Float, nullable=False)  # 終値（株式分割調整前）
    open_price = Column(Float, nullable=False)  # 始値
    high_price = Column(Float, nullable=False)  # 高値
    low_price = Column(Float, nullable=False)  # 安値
    close_price = Column(Float, nullable=False)  # 終値
    volume = Column(Integer, nullable=False)  # 出来高

    @declared_attr
    def stock_id(cls):
        """銘柄ID（FK）
        ※インスタンス変数として持たせておくとForeignKeyは例外が発生したので、
        declared_attrデコレータと共に定義してあります。

        Returns:
            銘柄ID
        """
        return Column(Integer, ForeignKey('stock.id', ondelete='CASCADE'))

    @classmethod
    def get_tablename(cls, stock):
        """テーブル名を取得します。
        銘柄ごとにテーブルを分けるため、銘柄ごとにユニークな名前を返します。

        Args:
            stock: 銘柄情報

        Returns:
            テーブル名（str）
        """
        return 'history_{}'.format(stock.symbol.lower())

    @classmethod
    def get_classname(cls, stock):
        """銘柄情報に基づきクラス名を取得します。

        Args:
            stock: 銘柄情報

        Returns:
            クラス名（str）
        """
        return 'History{}'.format(stock.id)

    @classmethod
    def create_table(cls, stock):
        """指定された銘柄の履歴テーブルを作成します。

        Args:
            銘柄を作成するテーブル
        """
        tablename = cls.get_tablename(stock)
        if not engine.has_table(tablename):
            # まだ存在しない場合はHistory_SYMBOLテーブルを作成します。
            klass = cls.get_class(stock, skip_has_table=True)
            Base.metadata.create_all(engine, tables=[klass.__table__])

    @classmethod
    def get_class(cls, stock, skip_has_table=False):
        """HistoryBaseのサブクラスを取得します。クラスがまだ定義されていない場合は定義します。

        Args:
            stock: 銘柄情報
            skip_has_table: Trueにするとテーブル作成をスキップします。

        Returns:
            HistoryBaseのサブクラス
        """
        tablename = cls.get_tablename(stock)
        classname = cls.get_classname(stock)

        if not skip_has_table and not engine.has_table(tablename):
            # テーブルチェックありで、かつテーブルが無い場合はNoneを返します。
            return None

        if classname in DEFINED_TABLE_CLASSES:
            klass = DEFINED_TABLE_CLASSES[classname]

        else:
            klass = type(classname, (HistoryBase, Base), {'__tablename__': tablename})
            DEFINED_TABLE_CLASSES[classname] = klass

        return klass

    @classmethod
    def save(cls, session, date, open_price, high_price,
             low_price, raw_close_price, close_price, volume):
        """レコードを新規作成・更新します。

        Args:
            session: SQLAlchemyのセッションオブジェクト
            以下略
        """
        q = session.query(cls).filter_by(date=date)
        if session.query(q.exists()).scalar():
            # レコードが既に存在する場合は取得して上書きします。
            create_flag = False
            hist = q.one()

        else:
            # レコードが存在しない場合は新規作成します。
            create_flag = True
            hist = cls()
            hist.date = date

        hist.open_price = str_to_number(open_price)
        hist.high_price = str_to_number(high_price)
        hist.low_price = str_to_number(low_price)
        hist.raw_close_price = str_to_number(raw_close_price)
        hist.close_price = str_to_number(close_price)
        hist.volume = str_to_number(volume, int)

        if create_flag:
            session.add(hist)

    @property
    def rate(self):
        """調整後の終値と、調整前の終値の比率を取得します。

        Returns:
            調整後の終値 / 調整前の終値
        """
        return self.close_price / self.raw_close_price


class FinancialData(Base):
    """ファイナンシャル情報を保持するクラスです。"""
    __tablename__ = 'financial_data'
    __table_args__ = (
        UniqueConstraint('stock_id', 'year'),  # ユニーク制約を追加します。
    )

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stock.id', ondelete='CASCADE'),
                      index=True, nullable=False)  # 銘柄ID
    year = Column(SmallInteger, nullable=False)  # 年度
    revenue = Column(Float, nullable=True)  # 売上
    net_income = Column(Float, nullable=True)  # 純利益
    cf_ope = Column(Float, nullable=True)  # キャッシュフロー（営業活動）
    cf_inv = Column(Float, nullable=True)  # キャッシュフロー（投資活動）
    cf_fin = Column(Float, nullable=True)  # キャッシュフロー（財務活動）
    created_at = Column(DateTime, default=datetime.now())  # 作成日時
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())  # 更新日時

    @classmethod
    def save(cls, session, stock, year, revenue, net_income,
             cf_ope, cf_inv, cf_fin):
        """レコードを新規作成・更新します。

        Args:
            session: SQLAlchemyのセッションオブジェクト
            以下略
        """
        q = session.query(cls).filter_by(stock_id=stock.id, year=year)

        if session.query(q.exists()).scalar():
            create_flag = False
            f = q.one()

        else:
            create_flag = True
            f = cls()
            f.stock_id = stock.id
            f.year = year

        f.revenue = revenue or None
        f.net_income = net_income or None
        f.cf_ope = cf_ope or None
        f.cf_inv = cf_inv or None
        f.cf_fin = cf_fin or None

        # 型を変換します。
        f.revenue = str_to_number(f.revenue)
        f.net_income = str_to_number(f.net_income)
        f.cf_ope = str_to_number(f.cf_ope)
        f.cf_inv = str_to_number(f.cf_inv)
        f.cf_fin = str_to_number(f.cf_fin)

        if create_flag:
            session.add(f)  # 新規作成します。


# FinancialDataテーブルを作成します。
Base.metadata.create_all(engine, tables=[FinancialData.__table__], checkfirst=True)
