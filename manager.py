#!/usr/bin/env python
# coding: utf-8
import os
import sys
import importlib
from ppyt.const import BASE_DIR

# locale.setlocale(locale.LC_ALL, 'en_US')
SCRIPT_DIR = os.path.join(BASE_DIR, 'commands')


def main():
    # パスを追加します。
    sys.path.append(BASE_DIR)

    # 実行するコマンドを決定します。
    if len(sys.argv) <= 1:
        show_command_list()  # コマンド一覧を表示して終了します。

    else:
        # 実行するコマンド名と、そのコマンド名を除外した引数のリストを取得します。
        import argparse
        command, newargs = None, []
        parser = argparse.ArgumentParser()
        parser.add_argument('command', type=str, nargs=1)  # 最初のコマンドライン引数をコマンド名とします。
        for args in parser.parse_known_args():  # parse_known_argsで余分な引数を無視します。
            if hasattr(args, 'command'):
                # nargs=1を指定しているので、サイズ1のlistにコマンド名が入っています。
                command = args.command[0]
                continue
            newargs.extend(args)  # コマンド名以外を引数のリストに追加していきます。

    # 実行するスクリプトを決定します。
    if command is None or command + '.py' not in os.listdir(SCRIPT_DIR):
        show_command_list()  # コマンド一覧を表示して終了します。

    script_path = 'ppyt.commands.' + command

    # 実行するクラスのインスタンスを生成してキックします。
    module = importlib.import_module(script_path)
    try:
        instance = getattr(module, 'Command')(manager=os.path.basename(__file__),
                                              command=command, args=newargs)
    except Exception as e:
        print(e)
        print('コマンドを実行できませんでした。'
              '{}がCommandBaseを継承しているかを確認してください。'.format(module.__name__))
        exit()
    instance.start()


def show_command_list():
    print('# コマンド一覧')
    for filename in os.listdir(SCRIPT_DIR):
        command, ext = os.path.splitext(filename)
        if ext != '.py' or command.startswith('_'):
            continue
        print('* ' + command)
    exit()


if __name__ == '__main__':
    main()
