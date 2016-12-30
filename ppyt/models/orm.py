# coding: utf-8
import logging
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import (
    create_engine, event, Column, Integer, String,
    Float, Date, DateTime, SmallInteger, Boolean,
    ForeignKeyConstraint
)
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
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


@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    import sqlite3
    if type(dbapi_connection) == sqlite3.Connection:
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.close()


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


class Stock(Base):
    """銘柄の情報を持つクラスです。"""
    __tablename__ = 'stock'
    __table_args__ = (
        ForeignKeyConstraint(['sector_id'], ['sector.id'], ondelete='RESTRICT'),
    )
    SYMBOL_LENGTH = 16  # symbolカラムの長さを定義します。

    symbol = Column(String(SYMBOL_LENGTH), primary_key=True)  # 銘柄のシンボル
    name = Column(String(64), nullable=False)  # 銘柄の名前
    market_id = Column(Integer, nullable=False)  # マーケットID
    sector_id = Column(Integer, index=True, nullable=False)  # セクターID
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
            query = session.query(History).filter_by(symbol=self.symbol)

            if self.start_date is not None:
                # start_dateが設定されている場合は絞り込み条件に追加します。
                query = query.filter(History.date >= self.start_date)

            if self.end_date is not None:
                # end_dateが設定されている場合は絞り込み条件に追加します。
                query = query.filter(History.date <= self.end_date)

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


class HistoryBase(object):
    """履歴情報（日毎の始値、終値などを保存持つ）の親クラスです。"""
    __table_args__ = (
        ForeignKeyConstraint(['symbol'], ['stock.symbol'],
                             onupdate='CASCADE', ondelete='CASCADE'),
    )

    symbol = Column(String(Stock.SYMBOL_LENGTH), primary_key=True)
    date = Column(Date, primary_key=True)  # 日付
    raw_close_price = Column(Float, nullable=False)  # 終値（株式分割調整前）
    open_price = Column(Float, nullable=False)  # 始値
    high_price = Column(Float, nullable=False)  # 高値
    low_price = Column(Float, nullable=False)  # 安値
    close_price = Column(Float, nullable=False)  # 終値
    volume = Column(Integer, nullable=False)  # 出来高

    @classmethod
    def save(cls, session, symbol, date, open_price, high_price,
             low_price, raw_close_price, close_price, volume):
        """レコードを新規作成・更新します。

        Args:
            session: SQLAlchemyのセッションオブジェクト
            以下略
        """
        q = session.query(cls).filter_by(symbol=symbol, date=date)

        if session.query(q.exists()).scalar():
            # レコードが既に存在する場合は取得して上書きします。
            create_flag = False
            hist = q.one()

        else:
            # レコードが存在しない場合は新規作成します。
            create_flag = True
            hist = cls()
            hist.symbol = symbol
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


class History(HistoryBase, Base):
    __tablename__ = 'history'


class FinancialData(Base):
    """ファイナンシャル情報を保持するクラスです。"""
    __tablename__ = 'financial_data'
    __table_args__ = (
        # UniqueConstraint('symbol', 'year', 'quarter'),
        ForeignKeyConstraint(['symbol'], ['stock.symbol'],
                             onupdate='CASCADE', ondelete='CASCADE'),
    )

    symbol = Column(String(Stock.SYMBOL_LENGTH), primary_key=True)
    period = Column(String(6), primary_key=True)  # 期を表すコード 例: 16A, 16Q1
    year = Column(SmallInteger, nullable=False)  # 年度
    quarter = Column(SmallInteger, nullable=True, default=None)  # Quarter
    filing_date = Column(Date, nullable=False)  # Filing Date
    revenue = Column(Float, nullable=True)  # 売上
    net_income = Column(Float, nullable=True)  # 純利益
    cf_ope = Column(Float, nullable=True)  # キャッシュフロー（営業活動）
    cf_inv = Column(Float, nullable=True)  # キャッシュフロー（投資活動）
    cf_fin = Column(Float, nullable=True)  # キャッシュフロー（財務活動）
    created_at = Column(DateTime, default=datetime.now())  # 作成日時
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())  # 更新日時

    @staticmethod
    def get_period(year, quarter):
        """期を表す文字列を取得します。"""
        if quarter is None:
            return '{}A'.format(year)

        return '{}Q{}'.format(year, quarter)

    @classmethod
    def save(cls, session, stock, year, quarter, filing_date, revenue, net_income,
             cf_ope, cf_inv, cf_fin):
        """レコードを新規作成・更新します。

        Args:
            session: SQLAlchemyのセッションオブジェクト
            以下略
        """
        period = cls.get_period(year=year, quarter=quarter)
        q = session.query(cls).filter_by(symbol=stock.symbol, period=period)

        if session.query(q.exists()).scalar():
            create_flag = False
            f = q.one()

        else:
            create_flag = True
            f = cls()
            f.symbol = stock.symbol
            f.period = period
            f.year = year
            f.quarter = quarter

        f.filing_date = filing_date

        if revenue:
            f.revenue = str_to_number(revenue)

        if net_income:
            f.net_income = str_to_number(net_income)

        if cf_ope:
            f.cf_ope = str_to_number(cf_ope)

        if cf_inv:
            f.cf_inv = str_to_number(cf_inv)

        if cf_fin:
            f.cf_fin = str_to_number(cf_fin)

        if create_flag:
            session.add(f)  # 新規作成します。


class Setting(Base):
    """設定情報を保存するクラスです"""
    __tablename__ = 'setting'
    KEY_DEFAULTRULEFILE = 'default_rulefile'
    KEY_DEFAULTFILTERFILE = 'default_filterfile'

    key = Column(String(64), primary_key=True)
    value = Column(String(200), nullable=False)

    @classmethod
    def get_list(cls):
        """key, valueの一覧を返します。"""
        with start_session() as session:
            return [row for row in session.query(cls).order_by('key')]

    @classmethod
    def get_keys(cls):
        """keyの一覧を取得します。"""
        return [row.key for row in cls.get_list()]

    @classmethod
    def get_value(cls, key):
        """keyに対応する値を取得します。"""
        with start_session() as session:
            row = session.query(cls).filter_by(key=key).one_or_none()
            return row.value if row else None

    @classmethod
    def register_initials(cls):
        """Keyが未登録の場合は初期値を設定します。"""
        keys = [cls.KEY_DEFAULTRULEFILE,
                cls.KEY_DEFAULTFILTERFILE]

        for key in keys:
            if cls.get_value(key)is None:
                cls.save(key, 'default')  # Keyが未登録の場合は追加します。

    @classmethod
    def save(cls, key, value):
        """設定を保存します。"""
        with start_session(commit=True) as session:
            row = session.query(cls).filter_by(key=key).one_or_none()

            if not row:  # 新規作成の場合
                row = cls()
                row.key = key
                row.value = value
                session.add(row)

            else:  # 更新の場合
                row.value = value


# テーブルを作成します。
Base.metadata.create_all(engine, tables=[Sector.__table__], checkfirst=True)
Base.metadata.create_all(engine, tables=[Stock.__table__], checkfirst=True)
Base.metadata.create_all(engine, tables=[FinancialData.__table__], checkfirst=True)
Base.metadata.create_all(engine, tables=[History.__table__], checkfirst=True)
Base.metadata.create_all(engine, tables=[Setting.__table__], checkfirst=True)
