#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, TYPE_CHECKING

from abc import ABCMeta, abstractclassmethod
import tkinter as tk

from PokeConDialogue import PokeConDialogue

if TYPE_CHECKING:
    from Window import PokeControllerApp
    from Commands.Sender import Sender

# CommandBaseにGUIに関連する関数を集約する。
# print/widget関連

class Command:
    __metaclass__ = ABCMeta
    text_area_1 = None
    text_area_2 = None
    stdout_destination = '1'
    isPause = False
    canvas = None
    isGuide = False
    isSimilarity = False
    isImage = False
    profilename = None

    def __init__(self):
        self.isRunning = False
        
        self.message_dialogue = None

    @abstractclassmethod
    def start(self, ser: Sender, postProcess: PokeControllerApp.stopPlayPost = None):
        pass

    @abstractclassmethod
    def end(self, ser: Sender):
        pass

    def checkIfAlive(self):
        pass

    ############### print functions ###############
    def print_s(self, text: str):
        print(text)

    def print_t1(self, text: int | float | str | list | dict):
        '''
        上側のログ画面に文字列を出力する
        '''
        try:
            self.text_area_1.config(state='normal')
            self.text_area_1.insert('end', str(text) + '\n')
            self.text_area_1.config(state='disable')
            self.text_area_1.see("end")
        except:
            print(text)

    def print_t2(self, text: int | float | str | list | dict):
        '''
        上側のログ画面に文字列を出力する
        '''
        try:
            self.text_area_2.config(state='normal')
            self.text_area_2.insert('end', str(text) + '\n')
            self.text_area_2.config(state='disable')
            self.text_area_2.see("end")
        except:
            print(text)

    def print_t(self, text: int | float | str | list | dict):
        '''
        標準出力先として割り当てられていない方のログ画面に文字列を出力する
        '''
        if self.stdout_destination == '1':
            self.print_t2(text)
        elif self.stdout_destination == '2':
            self.print_t1(text)

    def print_ts(self, text: int | float | str | list | dict):
        '''
        標準出力先として割り当てられている方のログ画面に文字列を出力する
        '''
        if self.stdout_destination == '1':
            self.print_t1(text)
        elif self.stdout_destination == '2':
            self.print_t2(text)

    def print_t1b(self, mode, text: int | float | str | list | dict = ''):
        '''
        上側のログ画面に文字列を出力する
        mode: ['w'/'a'/'d'] 'w'上書き, 'a'追記, 'd'削除
        '''
        try:
            self.text_area_1.config(state='normal')
            if mode in ['w', 'd']:
                self.text_area_1.delete('1.0', 'end')
            if mode == 'w':
                self.text_area_1.insert('1.0', str(text))
            elif mode == 'a':
                self.text_area_1.insert('end', str(text))
            self.text_area_1.config(state='disable')
            self.text_area_1.see("end")
        except:
            pass

    def print_t2b(self, mode, text: int | float | str | list | dict = ''):
        '''
        下側のログ画面に文字列を出力する
        mode: ['w'/'a'/'d'] 'w'上書き, 'a'追記, 'd'削除
        '''
        try:
            self.text_area_2.config(state='normal')
            if mode in ['w', 'd']:
                self.text_area_2.delete('1.0', 'end')
            if mode == 'w':
                self.text_area_2.insert('1.0', str(text))
            elif mode == 'a':
                self.text_area_2.insert('end', str(text))
            self.text_area_2.config(state='disable')
            self.text_area_2.see("end")
        except:
            pass

    def print_tb(self, mode, text: int | float | str | list | dict = ''):
        '''
        標準出力先として割り当てられていない方のログ画面に文字列を出力する
        mode: ['w'/'a'/'d'] 'w'上書き, 'a'追記, 'd'削除
        '''
        if self.stdout_destination == '1':
            self.print_t2b(mode, text)
        elif self.stdout_destination == '2':
            self.print_t1b(mode, text)

    def print_tbs(self, mode, text: int | float | str | list | dict = ''):
        '''
        標準出力先として割り当てられている方のログ画面に文字列を出力する
        mode: ['w'/'a'/'d'] 'w'上書き, 'a'追記, 'd'削除
        '''
        if self.stdout_destination == '1':
            self.print_t1b(mode, text)
        elif self.stdout_destination == '2':
            self.print_t2b(mode, text)

    def dialogue(self, title: str, message: int | str | list, need: type = list) -> list | dict:
        self.message_dialogue = tk.Toplevel()
        ret = PokeConDialogue(self.message_dialogue, title, message).ret_value(need)
        self.message_dialogue = None
        return ret

    def dialogue6widget(self, title: str, dialogue_list: list, need: type = list) -> list | dict:
        self.message_dialogue = tk.Toplevel()
        ret = PokeConDialogue(self.message_dialogue, title, dialogue_list, mode=1).ret_value(need)
        self.message_dialogue = None
        return ret

if __name__ == "__main__":
    pass
