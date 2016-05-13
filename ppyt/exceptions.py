# coding: utf-8
import os


class NoDataError(Exception):
    """historyやindicatorのデータにアクセスした際に、取得対象のデータが存在しない場合に発生する例外です。
    データが存在しない場合は「データが足りていない（※1）」や「範囲外へのアクセス（※2）」などがあります。
    ※1: 25日移動平均線の場合、1から24日目まではデータがないので集計できません。
    ※2: 明日以降などのデータにはアクセスできないようになっています。"""
    pass


class OrderTypeError(Exception):
    """予期せぬorder_typeが見つかったときに発生する例外です。プログラムにバグがあるので修正する必要があります。"""

    def __init__(self, order_type):
        """コンストラクタ

        Args:
            order_type: プログラム中で出現した未知の注文種別
        """
        super().__init__('未知のorder_type [{}] が見つかりました。プログラムを修正してください。'
                         .format(order_type))

class CommandError(Exception):
    """コマンド失敗時に発生する例外です。各コマンドはこの例外を受けたら処理を停止し、
    画面にメッセージを表示します。"""
    pass


class DuplicateFindkeyError(CommandError):  # 継承OK?
    """FinderMixinを継承したクラスのクラス変数__findekey__が重複している場合に発生する例外です。
    この例外を見たら_findkeyの重複を解決する必要があります。"""

    def __init__(self, rule_type, findkey):
        """コンストラクタ

        Args:
            rule_type: findkeyの種別（indicaotrsやconditionsなど）
            findkey: クラスを一意に特定するためのキー
        """
        super().__init__('{}のfindkey: [{}] が重複しています。'.format(rule_type, findkey))


class NewInstanceError(CommandError):  # 継承OK?
    """インスタンス生成に失敗した場合に発生する例外です。
    大抵はルールファイルを見直す必要があります。"""

    def __init__(self, msg=None, rule_type=None, findkey=None, classname=None, err=None):
        """コンストラクタ

        Args:
            msg: メッセージ
            rule_type: findkeyの種別（indicaotrsやconditionsなど）
            findkey: クラスを一意に特定するためのキー
            classname: クラス名
            err: 発生した例外
                ※abstractmethodをオーバーライドしていない場合や、
                設定ファイルの引数のミスなどで発生した例外がセットされています。
                引数のミスに関しては、プログラム側でチェックして、
                予期せぬ例外が発生しないようにした方が原因が判明しやすくなります。
                なお、引数をチェックする場合はArgumentErrorをご利用ください。
        """
        msgarr = []
        msgarr.append('インスタンスの生成に失敗しました。')

        if rule_type:
            msgarr.append('rule_type: {}'.format(rule_type))

        if findkey:
            msgarr.append('findkey: {}'.format(findkey))

        if classname:
            msgarr.append('クラス名: {}'.format(classname))

        if msg:
            msgarr.append(str(msg))

        if err:
            msgarr.append('例外: {}'.format(err))

        super().__init__(os.linesep.join(msgarr))


class ArgumentError(CommandError):
    """引数に誤りがあった場合に発生する例外です。"""

    def __init__(self, name, strtype=None):
        """
        Args:
            name: 引数の名前
            strtype: 引数の正しい型（文字列）
        """
        msg = '引数[{}]が指定されていないか、型が正しくありません。'.format(name)
        if strtype is not None:
            msg += '型は[{}]で指定してください。'.format(strtype)

        super().__init__(msg)
