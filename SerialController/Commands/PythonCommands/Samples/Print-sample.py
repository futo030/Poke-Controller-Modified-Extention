#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Commands.PythonCommandBase import PythonCommand


class Print_sample(PythonCommand):
    NAME = 'Print出力(sample)'

    def __init__(self):
        super().__init__()

    def do(self):
        print("通常のprint出力です。")
        self.print_s("通常のprint出力です。(CommandBase)")

        self.print_t1("上側に文字を出力します。")
        self.print_t2("下側に文字を出力します。")
        self.print_t("標準出力が割り当てられていない方のログ画面に文字を出力します。")

        self.print_t1b("w", "上側に文字を出力します。(上書きモードです)")
        self.print_t2b("w", "下側に文字を出力します。(上書きモードです)")
        self.print_tb("w", "標準出力が割り当てられていない方のログ画面に文字を出力します。(上書きモードです)")
        self.print_t1b("a", "上側に文字を出力します。(追記モードです)")
        self.print_t2b("a", "下側に文字を出力します。(追記モードです)")
        self.print_tb("a", "標準出力が割り当てられていない方のログ画面に文字を出力します。(追記モードです)")
        # self.print_t1b("d")   # 上側のログ画面をクリアします
        # self.print_t2b("d")   # 下側のログ画面をクリアします
        # self.print_tb("d")    # 標準出力が割り当てられていない方のログ画面をクリアします

        self.finish()
