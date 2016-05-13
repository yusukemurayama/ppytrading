# coding: utf-8
import logging

logger = logging.getLogger(__name__)


def str_to_number(value, totype=float):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    elif isinstance(value, str):
        value = value.replace(',', '')
        return totype(value)
    else:
        raise Exception('str_to_numberの引数に予期せぬ型[{}]が指定されました。'
                        .format(type(value)))


def format_for_date(date):
    """YYYY年MM月DD日という文字列を取得します。

    Args:
        date: datetime.date型のオブジェクト

    Returns:
        YYYY麺MM月DD日という形式のstr型オブジェクト
    """
    return date.strftime('%Y-%m-%d') if date else '---'


def format_with_comma(value):
    """カンマ区切りの文字列を取得します。

    Args:
        value: カンマ区切りに変換するint, float型変数

    Returns:
        カンマ区切りになったstr型オブジェクト
    """
    try:
        float(value)
    except ValueError:
        raise Exception('format_with_commaでfloatに変換できませんでした。'
                        '引数の型が[{}]になっています。'.format(type(value)))
    return '{:,}'.format(round(value, 2))


def format_with_padding(value, length, align='l'):
    """
    前後にスペースを入れた文字列を取得します。

    Args:
        length: スペース追加後の横幅
        align:
            c, center: 中央寄せ
            r, right: 右寄せ
            それ以外: 左寄せ

    Returns:
        スペースを追加した文字列
    """
    import math

    if type(value) != str:
        value = str(value)

    # 前後の空白を削除します。
    value = value.strip()

    # 半角文字、全角文字の数を調べます。
    han_count = len([c for c in value if ord(c) >= 0x20 and ord(c) <= 0x7e])
    zen_count = len(value) - han_count

    # 挿入するスペースの数を決定します。
    pad_spaces = length - (han_count + zen_count * 2)

    if pad_spaces <= 0:
        return value

    if align in ('c', 'center'):  # 真ん中寄せの場合
        ps_left = int(math.floor(pad_spaces / 2))
        ps_right = int(math.ceil(pad_spaces / 2))

    elif align in ('r', 'right'):  # 右寄せの場合
        ps_left, ps_right = pad_spaces - 1, 1

    else:  # それ以外は左寄せ
        ps_left, ps_right = 1, pad_spaces - 1

    return ' ' * ps_left + value + ' ' * ps_right
