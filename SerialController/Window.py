#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys
import os
import re
from os.path import dirname, abspath
import cv2
import platform
import subprocess
import threading
import Window
import tkinter.ttk as ttk
import tkinter.messagebox as tkmsg
import tkinter.scrolledtext as st
from time import sleep
from serial.tools import list_ports
from logging import getLogger, DEBUG, NullHandler
from pygubu.widgets.scrollbarhelper import ScrollbarHelper

from Camera import Camera
import Settings
from CommandLoader import CommandLoader
from GuiAssets import CaptureArea, ControllerGUI
from KeyConfig import PokeKeycon
from Keyboard import SwitchKeyboardController
from LineNotify import Line_Notify
from Menubar import PokeController_Menubar
import PokeConLogger
import Utility as util
from Commands import McuCommandBase, PythonCommandBase, Sender
from Commands.Keys import KeyPress
from Commands.CommandBase import Command

addpath = dirname(dirname(dirname(abspath(__file__))))	#SerialControllerフォルダのパス
sys.path.append(addpath)

NAME = "Poke-Controller Modified Extension"
VERSION = "ver.0.0.0.0.2"

class PokeControllerApp:
    def __init__(self, master=None, profile='default'):

        self._logger = getLogger(__name__)
        self._logger.addHandler(NullHandler())

        self._logger.setLevel(DEBUG)
        self._logger.propagate = True

        self._logger.debug(f'User Profile Name: \'{profile}\'')

        self.root = master
        self.root.title(NAME + ' ' + VERSION + f" (profile: {args.profile})")
        # self.root.resizable(0, 0)
        self.controller = None
        self.poke_treeview = None
        self.keyPress = None
        self.keyboard = None

        self.camera_dic = None
        self.Line = None

        self.pokeconname = NAME
        self.pokeconversion = VERSION[4:]

        Command.profilename = profile

        '''
        ここから
        '''
        # build ui
        self.main_frame = ttk.Frame(master)
        self.camera_lf = ttk.Labelframe(self.main_frame)
        self.top_command_f = ttk.Frame(self.camera_lf)
        self.start_top_button = ttk.Button(self.top_command_f)
        self.start_top_button.configure(text='Start')
        self.start_top_button.grid(column='0', padx='5', pady='5', row='0', sticky='ew')
        self.start_top_button.configure(command=self.startPlay)
        self.simplecon_top_button = ttk.Button(self.top_command_f)
        self.simplecon_top_button.configure(text='Controller')
        self.simplecon_top_button.grid(column='1', padx='5', pady='5', row='0', sticky='ew')
        self.simplecon_top_button.configure(command=self.createControllerWindow)
        self.clear_top_button = ttk.Button(self.top_command_f)
        self.clear_top_button.configure(text='Clear Outputs')
        self.clear_top_button.grid(column='2', padx='5', pady='5', row='0')
        self.clear_top_button.configure(command=self.clearOutputs)
        self.capture_button = ttk.Button(self.top_command_f)
        self.capture_button.configure(text='Capture')
        self.capture_button.grid(column='3', padx='5', pady='5', row='0', sticky='ew')
        self.capture_button.configure(command=self.saveCapture)
        self.open_capture_button = ttk.Button(self.top_command_f)
        self.open_folder_img = tk.PhotoImage(file="./assets/icons8-OpenDir-16.png") # modified
        self.open_capture_button.configure(image=self.open_folder_img)              # modified
        self.open_capture_button.grid(column='4', pady='5', row='0')
        self.open_capture_button.configure(command=self.OpenCaptureDir)
        self.line_button = ttk.Button(self.top_command_f)
        self.line_button.configure(text='Line')
        self.line_button.grid(column='5', padx='5', pady='5', row='0', sticky='ew')
        self.line_button.configure(command=self.sendLineImage)
        self.top_command_f.grid(column='0', row='0', sticky='w')
        self.top_command_f.grid_anchor('center')
        self.canvas_frame = ttk.Frame(self.camera_lf)
        self.canvas_frame.configure(height='360', relief='groove', width='640')
        self.canvas_frame.grid(column='0', columnspan='7', row='1')
        self.camera_lf.configure(text='Main Panel')  # modfied
        self.camera_lf.grid(column='0', columnspan='3', padx='5', pady='5', row='0', sticky='ew')
        self.camera_lf.rowconfigure('0', uniform='0')
        self.controller_nb = ttk.Notebook(self.main_frame)
        self.camera_f = ttk.Frame(self.controller_nb)
        self.camera_settings_lf = ttk.Labelframe(self.camera_f)
        self.camera_id_label = ttk.Label(self.camera_settings_lf)
        self.camera_id_label.configure(anchor='center', text='Camera ID: ')
        self.camera_id_label.grid(column='0', padx='5', pady='5', row='0', sticky='ew')
        self.camera_id_entry = ttk.Entry(self.camera_settings_lf)
        self.camera_id = tk.IntVar(value='')
        self.camera_id_entry.configure(state='readonly', textvariable=self.camera_id, width='7')
        self.camera_id_entry.grid(column='1', padx='5', pady='5', row='0', sticky='ew')
        self.fps_label = ttk.Label(self.camera_settings_lf)
        self.fps_label.configure(text='FPS: ')
        self.fps_label.grid(column='2', padx='5', pady='5', row='0', sticky='ew')
        self.fps_cb = ttk.Combobox(self.camera_settings_lf)
        self.fps = tk.StringVar(value='')
        self.fps_cb.configure(justify='right', state='readonly', textvariable=self.fps, values='60 45 30 15 5')
        self.fps_cb.configure(width='5')
        self.fps_cb.grid(column='3', padx='10', pady='5', row='0', sticky='ew')
        self.fps_cb.bind('<<ComboboxSelected>>', self.applyFps, add='')
        self.show_size_label = ttk.Label(self.camera_settings_lf)
        self.show_size_label.configure(text='Show Size: ')
        self.show_size_label.grid(column='4', padx='5', pady='5', row='0', sticky='ew')
        self.show_size_cb = ttk.Combobox(self.camera_settings_lf)
        self.show_size = tk.StringVar(value='')
        self.show_size_cb.configure(state='readonly', textvariable=self.show_size, values='640x360 960x540 1280x720 1920x1080')
        self.show_size_cb.grid(column='5', padx='5', row='0', sticky='ew')
        self.show_size_cb.bind('<<ComboboxSelected>>', self.applyWindowSize, add='')
        self.camera_separator = ttk.Separator(self.camera_settings_lf)
        self.camera_separator.configure(orient='vertical')
        self.camera_separator.grid(column='6', padx='5', pady='5', row='0', sticky='ns')
        self.reload_button = ttk.Button(self.camera_settings_lf)
        self.reload_button.configure(text='Reload Camera')
        self.reload_button.grid(column='7', padx='5', pady='5', row='0', sticky='ew')
        self.reload_button.configure(command=self.openCamera)
        self.camera_name_label = ttk.Label(self.camera_settings_lf)
        self.camera_name_label.configure(anchor='center', text='Camera Name: ')
        self.camera_name_label.grid(column='0', padx='5', pady='5', row='1', sticky='ew')
        self.camera_name_cb = ttk.Combobox(self.camera_settings_lf)
        self.camera_name_fromDLL = tk.StringVar(value='')
        self.camera_name_cb.configure(state='normal', textvariable=self.camera_name_fromDLL)
        self.camera_name_cb.grid(column='1', columnspan='7', padx='5', pady='5', row='1', sticky='ew')
        self.camera_name_cb.bind('<<ComboboxSelected>>', self.set_cameraid, add='')
        self.camera_settings_lf.configure(text='Settings', width='420')
        self.camera_settings_lf.grid(column='0', padx='5', row='0', sticky='ew')
        self.display_settings_lf = ttk.Labelframe(self.camera_f)
        self.show_realtime_checkbox = ttk.Checkbutton(self.display_settings_lf)
        self.is_show_realtime = tk.BooleanVar() # modified
        self.show_realtime_checkbox.configure(text='Show Realtime', variable=self.is_show_realtime)
        self.show_realtime_checkbox.grid(column='0', padx='5', pady='5', row='0', sticky='ew')
        self.show_guide_checkbox = ttk.Checkbutton(self.display_settings_lf)
        self.is_show_guide = tk.BooleanVar() # modified
        self.show_guide_checkbox.configure(text='Show Guide', variable=self.is_show_guide)
        self.show_guide_checkbox.grid(column='1', padx='5', pady='5', row='0', sticky='ew')
        self.show_guide_checkbox.configure(command=self.mode_change_show_guide)
        self.display_settings_lf.configure(height='200', text='Display Settings', width='200')
        self.display_settings_lf.grid(column='0', padx='5', pady='5', row='1', sticky='ew')
        # self.camera_f.configure(height='200', width='200')    # removed
        self.camera_f.pack(side='top')
        self.controller_nb.add(self.camera_f, padding='5', sticky='nsew', text='Camera')
        self.serial_f = ttk.Frame(self.controller_nb)
        self.settings_lf = ttk.Labelframe(self.serial_f)
        self.com_port_label = ttk.Label(self.settings_lf)
        if platform.system() == "Windows" or platform.system() == "Darwin":
            self.com_port_label.configure(text='COM Port: ')
        else:
            self.com_port_label.configure(text='Port: ')
        self.com_port_label.grid(column='0', padx='5', pady='5', row='0', sticky='ew')
        # self.label2.rowconfigure('0', uniform='None', weight='0')   # added
        self.com_port_entry = ttk.Entry(self.settings_lf)
        self.com_port = tk.IntVar(value='')
        self.com_port_name = tk.StringVar() # added
        self.com_port_entry.configure(state='readonly', textvariable=self.com_port, width='5')
        self.com_port_entry.grid(column='1', padx='10', pady='5', row='0', sticky='ew')
        # self.ecom_port_entryntry2.rowconfigure('0', uniform='None', weight='0')   # added
        self.settings_separator_1 = ttk.Separator(self.settings_lf)
        self.settings_separator_1.configure(orient='vertical')
        self.settings_separator_1.grid(column='2', pady='5', row='0', sticky='ns')
        self.baud_rate_label = ttk.Label(self.settings_lf)
        self.baud_rate_label.configure(text='Baud Rate: ')
        self.baud_rate_label.grid(column='3', padx='5', pady='5', row='0', sticky='ew')
        self.baud_rate_cb = ttk.Combobox(self.settings_lf)
        self.baud_rate = tk.StringVar(value='')
        self.baud_rate_cb.configure(justify='right', state='readonly', textvariable=self.baud_rate, values='9600 4800')
        self.baud_rate_cb.configure(width='6')
        self.baud_rate_cb.grid(column='4', padx='10', pady='5', row='0', sticky='ew')
        self.baud_rate_cb.bind('<<ComboboxSelected>>', self.applyBaudRate, add='')
        self.settings_separator_2 = ttk.Separator(self.settings_lf)
        self.settings_separator_2.configure(orient='vertical')
        self.settings_separator_2.grid(column='5', pady='5', row='0', sticky='ns')
        self.reload_com_port_button = ttk.Button(self.settings_lf)
        self.reload_com_port_button.configure(text='Reload Port')
        self.reload_com_port_button.grid(column='6', padx='10', pady='5', row='0', sticky='ew')
        self.reload_com_port_button.configure(command=self.activateSerial)
        # self.reload_com_port.rowconfigure('0', uniform='None', weight='0')    # added
        self.disconnect_com_port_button = ttk.Button(self.settings_lf)
        self.disconnect_com_port_button.configure(text='Disconnect Port')
        self.disconnect_com_port_button.grid(column='7', padx='10', pady='5', row='0', sticky='ew')
        self.disconnect_com_port_button.configure(command=self.inactivateSerial)
        # self.disconnect_com_port_button.rowconfigure('0', uniform='None', weight='0') # added
        self.serial_device_name_label = ttk.Label(self.settings_lf)
        self.serial_device_name_label.configure(anchor='center', text='Device Name: ')
        self.serial_device_name_label.grid(column='0', padx='5', pady='5', row='1', sticky='ew')
        self.serial_device_name_cb = ttk.Combobox(self.settings_lf)
        self.serial_device_name = tk.StringVar(value='(選択してください)')
        self.serial_device_name_cb.configure(state='normal', textvariable=self.serial_device_name)
        self.serial_device_name_cb.grid(column='1', columnspan='6', padx='5', pady='5', row='1', sticky='ew')
        self.serial_device_name_cb.bind('<<ComboboxSelected>>', self.set_device, add='')
        self.scan_device_button = ttk.Button(self.settings_lf)
        self.scan_device_button.configure(text='Scan Device')
        self.scan_device_button.grid(column='7', padx='10', pady='5', row='1', sticky='ew')
        self.scan_device_button.configure(command=self.locateDeviceCmbbox)
        self.settings_lf.configure(text='Settings')
        self.settings_lf.grid(column='0', padx='5', row='0', sticky='ew')
        self.serial_debug_lf = ttk.Labelframe(self.serial_f)
        self.show_serial_checkbox = ttk.Checkbutton(self.serial_debug_lf)
        self.is_show_serial = tk.BooleanVar()   # modified
        self.show_serial_checkbox.configure(text='Show Serial', variable=self.is_show_serial)
        self.show_serial_checkbox.pack(padx='5', pady='5', side='left')
        self.serial_debug_lf.configure(height='200', text='Debug', width='200')
        self.serial_debug_lf.grid(column='0', padx='5', row='1', sticky='ew')
        # self.serial_f.configure(height='200', width='200')    # removed
        self.serial_f.pack()
        self.controller_nb.add(self.serial_f, padding='5', sticky='nsew', text='Serial')
        self.manual_control_f = ttk.Frame(self.controller_nb)
        self.software_lf = ttk.Labelframe(self.manual_control_f)
        self.simplecon_button = ttk.Button(self.software_lf)
        self.simplecon_button.configure(text='Controller', width='15')
        self.simplecon_button.grid(column='0', padx='10', pady='5', row='0', sticky='ew')
        self.simplecon_button.configure(command=self.createControllerWindow)
        self.use_keyboard_checkbox = ttk.Checkbutton(self.software_lf)
        self.is_use_keyboard = tk.BooleanVar()  # modified
        self.use_keyboard_checkbox.configure(text='Use Keyboard', variable=self.is_use_keyboard)
        self.use_keyboard_checkbox.grid(column='0', padx='10', pady='5', row='1', sticky='ew')
        self.use_keyboard_checkbox.configure(command=self.activateKeyboard)
        self.left_stick_mouse_checkbox = ttk.Checkbutton(self.software_lf)
        self.camera_lf.is_use_left_stick_mouse = tk.BooleanVar()  # modified(継承いじるの面倒なので暫定的にこのまま)
        self.left_stick_mouse_checkbox.configure(text='Use LStick Mouse', variable=self.camera_lf.is_use_left_stick_mouse)  # modified
        self.left_stick_mouse_checkbox.grid(column='1', padx='10', pady='5', row='1', sticky='ew')
        self.left_stick_mouse_checkbox.configure(command=self.activate_Left_stick_mouse)
        self.right_stick_mouse_checkbox = ttk.Checkbutton(self.software_lf)
        self.camera_lf.is_use_right_stick_mouse = tk.BooleanVar() # modified(継承いじるの面倒なので暫定的にこのまま)
        self.right_stick_mouse_checkbox.configure(text='Use RStick Mouse', variable=self.camera_lf.is_use_right_stick_mouse)    # modified
        self.right_stick_mouse_checkbox.grid(column='2', padx='10', pady='5', row='1', sticky='ew')
        self.right_stick_mouse_checkbox.configure(command=self.activate_Right_stick_mouse)
        self.software_lf.configure(height='200', text='Software')
        self.software_lf.grid(padx='5', sticky='ew')
        self.manual_control_f.configure(height='200', width='200')
        self.manual_control_f.pack()
        self.controller_nb.add(self.manual_control_f, padding='5', text='Manual Control')
        self.commands_f = ttk.Frame(self.controller_nb)
        self.select_commands_f = ttk.Frame(self.commands_f)
        self.command_nb = ttk.Notebook(self.select_commands_f)
        self.py_cb = ttk.Combobox(self.command_nb)
        self.py_name = tk.StringVar(value='')
        self.py_cb.configure(state='readonly', textvariable=self.py_name, width='100')
        self.py_cb.pack(fill='x', padx='10', pady='5', side='bottom')
        self.command_nb.add(self.py_cb, padding='5', text='Python Command')
        self.mcu_cb = ttk.Combobox(self.command_nb)
        self.mcu_name = tk.StringVar(value='')
        self.mcu_cb.configure(state='readonly', textvariable=self.mcu_name, validate='focusin', width='100')
        self.mcu_cb.pack(fill='x', padx='10', pady='5', side='bottom')
        self.command_nb.add(self.mcu_cb, padding='5', text='Mcu Command')
        self.shortcut_f = ttk.Frame(self.command_nb)
        self.shortcut_button_1 = ttk.Button(self.shortcut_f)
        self.shortcut_1 = tk.StringVar(value='Shortcut(1)')
        self.shortcut_button_1.configure(textvariable=self.shortcut_1, width='7')
        self.shortcut_button_1.pack(expand='true', fill='both', padx='5', side='left')
        self.shortcut_button_1.configure(command=lambda:self.startShortcutPlay(num=1))
        self.shortcut_button_2 = ttk.Button(self.shortcut_f)
        self.shortcut_2 = tk.StringVar(value='Shortcut(2)')
        self.shortcut_button_2.configure(textvariable=self.shortcut_2, width='7')
        self.shortcut_button_2.pack(expand='true', fill='both', padx='5', side='left')
        self.shortcut_button_2.configure(command=lambda:self.startShortcutPlay(num=2))
        self.shortcut_button_3 = ttk.Button(self.shortcut_f)
        self.shortcut_3 = tk.StringVar(value='Shortcut(3)')
        self.shortcut_button_3.configure(textvariable=self.shortcut_3, width='7')
        self.shortcut_button_3.pack(expand='true', fill='both', padx='5', side='left')
        self.shortcut_button_3.configure(command=lambda:self.startShortcutPlay(num=3))
        self.shortcut_button_4 = ttk.Button(self.shortcut_f)
        self.shortcut_4 = tk.StringVar(value='Shortcut(4)')
        self.shortcut_button_4.configure(textvariable=self.shortcut_4, width='7')
        self.shortcut_button_4.pack(expand='true', fill='both', padx='5', side='left')
        self.shortcut_button_4.configure(command=lambda:self.startShortcutPlay(num=4))
        self.shortcut_button_5 = ttk.Button(self.shortcut_f)
        self.shortcut_5 = tk.StringVar(value='Shortcut(5)')
        self.shortcut_button_5.configure(textvariable=self.shortcut_5, width='7')
        self.shortcut_button_5.pack(expand='true', fill='both', padx='5', side='left')
        self.shortcut_button_5.configure(command=lambda:self.startShortcutPlay(num=5))
        self.shortcut_f.configure(padding='5')
        self.shortcut_f.pack(side='top')
        self.command_nb.add(self.shortcut_f, padding='5', text='Shortcut')
        self.command_nb.configure(padding='0', width='580')
        self.command_nb.pack(padx='5', pady='5', side='left')
        self.command_nb.pack(fill="both", expand=True, padx='5', pady='5', side='left')
        self.command_nb.bind('<<NotebookTabChanged>>', self.controllButtons, add='')
        self.open_command_dir_button = ttk.Button(self.select_commands_f)
        self.open_command_dir_button.config(image=self.open_folder_img)
        self.open_command_dir_button.pack(fill="y", expand=False, side='left', ipadx='5', pady='15')
        self.open_command_dir_button.configure(command=self.OpenCommandDir)
        # self.select_commands_f.configure(height='200', width='200')
        self.select_commands_f.grid(column='0', row='0', sticky='ew')
        self.action_commands_f = ttk.Frame(self.commands_f)
        self.set_shortcut_label = ttk.Label(self.action_commands_f)
        self.set_shortcut_label.configure(text='Set Shortcut: ')
        self.set_shortcut_label.grid(column='0', padx='5', pady='5', row='0', sticky='ew')
        self.set_shortcut_num_sb = ttk.Spinbox(self.action_commands_f)
        self.set_shortcut_num = tk.StringVar(value='')
        self.set_shortcut_num_sb.configure(from_='1', increment='1', justify='left', textvariable=self.set_shortcut_num)
        self.set_shortcut_num_sb.configure(to='5', width='7')
        self.set_shortcut_num_sb.delete('0', 'end')
        self.set_shortcut_num_sb.insert('0', '''(select)''')
        self.set_shortcut_num_sb.grid(column='1', row='0', sticky='ew')
        self.shortcut_set_button = ttk.Button(self.action_commands_f)
        self.shortcut_set_button.configure(takefocus=False, text='Set')
        self.shortcut_set_button.grid(column='2', padx='10', pady='5', row='0', sticky='ew')
        self.shortcut_set_button.configure(command=self.assignShortcutButton)
        self.commands_separator_1 = ttk.Separator(self.action_commands_f)
        self.commands_separator_1.configure(orient='vertical')
        self.commands_separator_1.grid(column='3', pady='5', row='0', sticky='ns')
        self.reload_command_button = ttk.Button(self.action_commands_f)
        self.reload_command_button.configure(text='Reload')
        self.reload_command_button.grid(column='4', padx='10', pady='5', row='0', sticky='ew')
        self.reload_command_button.configure(command=self.reloadCommands)
        self.start_button = ttk.Button(self.action_commands_f)
        self.start_button.configure(text='Start')
        self.start_button.grid(column='5', padx='10', pady='5', row='0', sticky='ew')
        self.start_button.configure(command=self.startPlay)
        self.pause_button = ttk.Button(self.action_commands_f)
        self.pause_button.configure(text='Pause')
        self.pause_button.grid(column='6', padx='10', pady='5', row='0', sticky='ew')
        self.pause_button.configure(command=self.pausePlay)
        self.action_commands_f.configure(height='200', width='200')
        self.action_commands_f.grid(column='0', pady='5', row='1', sticky='e')
        self.commands_f.configure(height='200', width='500')
        self.commands_f.pack(side='top')
        self.controller_nb.add(self.commands_f, padding='5', text='Commands')
        self.others_f = ttk.Frame(self.controller_nb)
        self.othres_outputs_lf = ttk.Labelframe(self.others_f)
        self.outputs_size_adjuster_lf = ttk.Labelframe(self.othres_outputs_lf)
        self.area_size_scale = ttk.Scale(self.outputs_size_adjuster_lf)        
        self.area_size = tk.IntVar(value=20)
        self.area_size_scale.configure(from_='3', length='200', orient='horizontal', to='37')
        self.area_size_scale.configure(value='20', variable=self.area_size)
        self.area_size_scale.grid(column='0', padx='5', pady='5', row='0', sticky='ew')
        self.area_size_scale.configure(command=self.changeAreaSize)
        self.outputs_size_adjuster_lf.configure(text='Size Adjuster')
        self.outputs_size_adjuster_lf.grid(column='0', padx='5', pady='5', row='0', sticky='ew')
        self.outputs_stdout_dest_lf = ttk.Labelframe(self.othres_outputs_lf)
        self.stdout_destination_1_rb = ttk.Radiobutton(self.outputs_stdout_dest_lf)
        self.stdout_destination = tk.StringVar(value='1')
        self.stdout_destination_1_rb.configure(text='Output#1', value='1', variable=self.stdout_destination)
        self.stdout_destination_1_rb.grid(column='0', padx='5', pady='5', row='0', sticky='ew')
        self.stdout_destination_1_rb.configure(command=self.switchStdoutDestination)
        self.stdout_destination_2_rb = ttk.Radiobutton(self.outputs_stdout_dest_lf)
        self.stdout_destination_2_rb.configure(text='Output#2', value='2', variable=self.stdout_destination)
        self.stdout_destination_2_rb.grid(column='1', padx='5', pady='5', row='0', sticky='ew')
        self.stdout_destination_2_rb.configure(command=self.switchStdoutDestination)
        self.outputs_stdout_dest_lf.configure(text='Standard Output Destination')
        self.outputs_stdout_dest_lf.grid(column='1', padx='5', pady='5', row='0', sticky='ew')
        self.outputs_clear_lf = ttk.Labelframe(self.othres_outputs_lf)
        self.outputs_text_area_1_clear_button = ttk.Button(self.outputs_clear_lf)
        self.outputs_text_area_1_clear_button.configure(text='Clear(#1)')
        self.outputs_text_area_1_clear_button.grid(column='0', padx='10', pady='5', row='0', sticky='ew')
        self.outputs_text_area_1_clear_button.configure(command=self.clearTextArea1)
        self.outputs_text_area_2_clear_button = ttk.Button(self.outputs_clear_lf)
        self.outputs_text_area_2_clear_button.configure(text='Clear(#2)')
        self.outputs_text_area_2_clear_button.grid(column='1', padx='10', pady='5', row='0', sticky='ew')
        self.outputs_text_area_2_clear_button.configure(command=self.clearTextArea2)        
        self.outputs_clear_lf.configure(text='Clear Outputs')
        self.outputs_clear_lf.grid(column='2', padx='5', pady='5', row='0', sticky='ew')
        self.othres_outputs_lf.configure(height='200', text='Outputs', width='200')
        self.othres_outputs_lf.grid(column='0', padx='5', row='0', sticky='ew')
        self.others_help_lf = ttk.Labelframe(self.others_f)
        self.others_help_lf.configure(text='Help')
        self.others_help_lf.grid(column='0', padx='5', row='1', sticky='ew')
        self.others_f.configure(height='200', width='200')
        self.others_f.pack()
        self.controller_nb.add(self.others_f, sticky='nsew', text='Others')
        if platform.system() == "Windows" or platform.system() == "Darwin":
            self.controller_nb.configure(height='150', width='640')
        else:
            self.controller_nb.configure(height='180', width='640')
        self.controller_nb.grid(column='0', padx='5', pady='5', row='1', sticky='ew')
        self.output_area_lf = ttk.Labelframe(self.main_frame)
        self.output_area_lf.configure(text='Outputs')
        self.text_scroll_1 = ScrollbarHelper(self.output_area_lf, scrolltype='both')
        self.text_area_1 = tk.Text(self.text_scroll_1.container)
        self.text_area_1.config(blockcursor='true', height='20', insertunfocussed='none', maxundo='0')
        self.text_area_1.config(relief='flat', state='disabled', undo='false', width='50')
        self.text_area_1.pack(expand='true', fill='both', side='top')
        self.text_scroll_1.add_child(self.text_area_1)
        self.text_scroll_1.config(borderwidth='1', padding='1', relief='sunken')       
        # TODO - self.text_scroll_1: code for custom option 'usemousewheel' not implemented.
        self.text_scroll_1.pack(expand='true', fill='both', padx='5', pady='5', side='top')
        self.text_scroll_2 = ScrollbarHelper(self.output_area_lf, scrolltype='both')
        self.text_area_2 = tk.Text(self.text_scroll_2.container)
        self.text_area_2.config(blockcursor='true', height='20', insertunfocussed='none', maxundo='0')
        self.text_area_2.config(relief='flat', state='disabled', undo='false', width='50')
        self.text_area_2.pack(expand='true', fill='both', side='top')
        self.text_scroll_2.add_child(self.text_area_2)
        self.text_scroll_2.config(borderwidth='1', padding='1', relief='sunken')       
        self.text_scroll_2.pack(expand='true', fill='both', padx='5', pady='5', side='top')
        self.output_area_lf.grid(column='3', padx='5', pady='5', row='0', rowspan='2', sticky='nsew')
        self.main_frame.config(height='720', padding='5', relief='flat', width='1280')
        self.main_frame.pack(expand='true', fill='both', side='top')
        self.main_frame.columnconfigure('3', weight='1')
        '''
        ここまで
        '''

        # ToolTip設定
        self.start_top_button_tooltip = ToolTip(self.start_top_button, "自動化スクリプトを実行します")
        self.simplecon_top_button_tooltip = ToolTip(self.simplecon_top_button, "switch用ソフトウェアコントローラを起動します")
        self.clear_top_button_tooltip = ToolTip(self.clear_top_button, "ログ画面(output(#1)/output(#2))をクリアします")
        self.capture_button_tooltip = ToolTip(self.capture_button, "ゲーム画面のスクリーンショットを取得します")
        self.open_capture_button_tooltip = ToolTip(self.open_capture_button, "スクリーンショット画像を保存するディレクトリを開きます")
        self.line_button_tooltip = ToolTip(self.line_button, "現在のゲーム画像をLineに通知します")
        self.camera_id_label_tooltip = ToolTip(self.camera_id_label, "使用するキャプチャデバイスのIDを設定します")
        self.camera_id_entry_tooltip = ToolTip(self.camera_id_entry, "使用するキャプチャデバイスのID")
        self.reload_button_tooltip = ToolTip(self.reload_button, "設定したキャプチャデバイスとの接続を確立し、画像読み込みを開始します")
        self.fps_label_tooltip = ToolTip(self.fps_label, "FPSを設定します(即時反映)")
        self.fps_cb_tooltip = ToolTip(self.fps_cb, "設定されているFPS")
        self.show_size_label_tooltip = ToolTip(self.show_size_label, "表示する画像のサイズを設定します(即時反映)")
        self.show_size_cb_tooltip = ToolTip(self.show_size_cb, "表示されている画像のサイズ")
        self.camera_name_label_tooltip = ToolTip(self.camera_name_label, "使用するキャプチャデバイスを設定します")
        self.camera_name_cb_tooltip = ToolTip(self.camera_name_cb, "設定するキャプチャデバイス")
        self.show_realtime_checkbox_tooltip = ToolTip(self.show_realtime_checkbox, "画像をリアルタイムで更新する機能を有効化します\n(注意)本機能を有効化しないと画像は静止画のままとなります")
        self.show_guide_checkbox_tooltip = ToolTip(self.show_guide_checkbox, "ガイド表示を有効化します\n自動化スクリプト次第で本チェックボックスは無効化される場合があります")
        portheader = "COM" if platform.system() in ["Windows", "Darwin"] else ""
        self.com_port_label_tooltip = ToolTip(self.com_port_label, f"{portheader}ポート番号を設定します(デバイスマネージャーで確認可能です)")
        self.com_port_entry_tooltip = ToolTip(self.com_port_entry, f"設定する{portheader}ポート番号")
        self.baud_rate_label_tooltip = ToolTip(self.baud_rate_label, "ボーレートを設定します(switch:9600, GC:4800)")
        self.baud_rate_cb_tooltip = ToolTip(self.baud_rate_cb, "設定するボーレート")
        self.reload_com_port_button_tooltip = ToolTip(self.reload_com_port_button, "設定したCOMポート番号とボーレートの情報に基づいてUSBシリアルとの接続を確立します")
        self.disconnect_com_port_button_tooltip = ToolTip(self.disconnect_com_port_button, "USBシリアルとの接続を解除します")
        self.serial_device_name_label_tooltip = ToolTip(self.serial_device_name_label, "使用するシリアルデバイスを設定します")
        self.serial_device_name_cb_tooltip = ToolTip(self.serial_device_name_cb, "設定するシリアルデバイス名")
        self.scan_device_button_tooltip = ToolTip(self.scan_device_button, "シリアルデバイスをスキャンします")
        self.show_serial_checkbox_tooltip = ToolTip(self.show_serial_checkbox, "シリアル値を出力する機能を有効化します")
        self.simplecon_button_tooltip = ToolTip(self.simplecon_button, "switch用ソフトウェアコントローラを起動します")
        self.use_keyboard_checkbox_tooltip = ToolTip(self.use_keyboard_checkbox, "キーボードで操作する機能を有効化します")
        self.left_stick_mouse_checkbox_tooltip = ToolTip(self.left_stick_mouse_checkbox, "ゲーム画面上で左クリックを押下した後、その状態でマウスを動かすことで左stickを動かす機能を有効化します")
        self.right_stick_mouse_checkbox_tooltip = ToolTip(self.right_stick_mouse_checkbox, "ゲーム画面上で右クリックを押下した後、その状態でマウスを動かすことで右stickを動かす機能を有効化します")
        self.py_cb_tooltip = ToolTip(self.py_cb, "実行するスクリプト(python)")
        self.mcu_cb_tooltip = ToolTip(self.mcu_cb, "実行するスクリプト(mcu)")
        self.open_command_dir_button_tooltip = ToolTip(self.open_command_dir_button, "スクリプト(.py)を保存するディレクトリを開きます")
        self.set_shortcut_label_tooltip = ToolTip(self.set_shortcut_label, "ショートカットボタンに選択されているスクリプトを割り当てます")
        self.set_shortcut_num_sb_tooltip = ToolTip(self.set_shortcut_num_sb, "スクリプトを割り当てるショートカットボタンの番号")
        self.shortcut_set_button_tooltip = ToolTip(self.shortcut_set_button, "ショートカットボタンへのスクリプトの割り当てを実行します")
        self.reload_command_button_tooltip = ToolTip(self.reload_command_button, "自動化スクリプトを再度読み込みます")
        self.start_button_tooltip = ToolTip(self.start_button, "自動化スクリプトを実行します")
        self.pause_button_tooltip = ToolTip(self.pause_button, "自動化スクリプトを一時停止します")
        self.area_size_scale_tooltip = ToolTip(self.area_size_scale, "output(#1)(上側)とoutput(#2)(下側)の比率を調整します")
        self.stdout_destination_1_rb_tooltip = ToolTip(self.stdout_destination_1_rb, "標準出力先にoutput(#1)(上側)を設定します")
        self.stdout_destination_2_rb_tooltip = ToolTip(self.stdout_destination_2_rb, "標準出力先にoutput(#2)(下側)を設定します")
        self.outputs_text_area_1_clear_button_tooltip = ToolTip(self.outputs_text_area_1_clear_button, "output(#1)(上側)をクリアします")
        self.outputs_text_area_2_clear_button_tooltip = ToolTip(self.outputs_text_area_2_clear_button, "output(#2)(下側)をクリアします")
        # self.text_area_1_tooltip = ToolTip(self.text_area_1, "output(#1)")
        # self.text_area_2_tooltip = ToolTip(self.text_area_2, "output(#2)")

        # 仮置フレームを削除
        self.canvas_frame.destroy()

        # 標準出力をログにリダイレクト
        # sys.stdout = StdoutRedirector(self.text_area_1)
        # sys.stdout = StdoutRedirector(self.text_area_2)

        # ログ画面に自動化スクリプトからアクセスできるようにする。
        Command.text_area_1 = self.text_area_1
        Command.text_area_2 = self.text_area_2

        # 初期表示を出力
        self.text_area_1.config(state='normal')
        self.text_area_1.insert('1.0', '----------画面1----------\n')
        self.text_area_1.config(state='disable')
        self.text_area_2.config(state='normal')
        self.text_area_2.insert('1.0', '----------画面2----------\n')
        self.text_area_2.config(state='disable')

        # 引数設定時、使用するsetting.iniを変更
        print("User Profile Name:", Settings.GuiSettings.SETTING_PATH)
        profile_dirname = os.path.join('profiles', profile)
        if not os.path.isdir(profile_dirname):
            os.makedirs(profile_dirname)
            self._logger.debug(f'mkdir: \'{profile_dirname}\'')
        if profile != 'default':
            setting_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'profiles', profile, 'settings.ini')
            Settings.GuiSettings.SETTING_PATH = setting_path
            SwitchKeyboardController.SETTING_PATH = setting_path
            PokeKeycon.SETTING_PATH = setting_path
            self._logger.debug(f'Use Profile: \'{setting_path}\'')

        # load settings file
        self.loadSettings()
        # 各tk変数に設定値をセット(コピペ簡単のため)
        self.is_show_realtime.set(self.settings.is_show_realtime.get())
        self.is_show_guide.set(self.settings.is_show_guide.get())
        self.is_show_serial.set(self.settings.is_show_serial.get())
        self.is_use_keyboard.set(self.settings.is_use_keyboard.get())
        self.fps.set(self.settings.fps.get())
        self.show_size.set(self.settings.show_size.get())
        self.com_port.set(self.settings.com_port.get())
        self.com_port_name.set(self.settings.com_port_name.get())
        self.baud_rate.set(self.settings.baud_rate.get())
        self.camera_id.set(self.settings.camera_id.get())
        self.shortcut_command_name = { 
                                       1:self.settings.command_name_1.get(),
                                       2:self.settings.command_name_2.get(),
                                       3:self.settings.command_name_3.get(),
                                       4:self.settings.command_name_4.get(),
                                       5:self.settings.command_name_5.get()
                                      }
        # ショートカットに設定されたスクリプトのclass(python/mcu)はtk変数ではない
        self.shortcut_command_class = {
                                        1:self.settings.command_class_1,
                                        2:self.settings.command_class_2,
                                        3:self.settings.command_class_3,
                                        4:self.settings.command_class_4,
                                        5:self.settings.command_class_5
                                       }
        self.area_size.set(self.settings.area_size)
        self.stdout_destination.set(self.settings.stdout_destination)

        # Shortcutボタンに名称とtooltipを設定する
        self.shortcut_1.set(self.shortcut_command_name[1][:8])
        self.shortcut_2.set(self.shortcut_command_name[2][:8])
        self.shortcut_3.set(self.shortcut_command_name[3][:8])
        self.shortcut_4.set(self.shortcut_command_name[4][:8])
        self.shortcut_5.set(self.shortcut_command_name[5][:8])
        self.shortcut_button_1_tooltip = ToolTip(self.shortcut_button_1, self.shortcut_command_name[1])
        self.shortcut_button_2_tooltip = ToolTip(self.shortcut_button_2, self.shortcut_command_name[2])
        self.shortcut_button_3_tooltip = ToolTip(self.shortcut_button_3, self.shortcut_command_name[3])
        self.shortcut_button_4_tooltip = ToolTip(self.shortcut_button_4, self.shortcut_command_name[4])
        self.shortcut_button_5_tooltip = ToolTip(self.shortcut_button_5, self.shortcut_command_name[5])

        # self.shortcut_button_1["text"] = self.settings.command_name_1
        # 各コンボボックスを現在の設定値に合わせて表示
        self.fps_cb.current(self.fps_cb['values'].index(self.fps.get()))
        self.show_size_cb.current(
            self.show_size_cb['values'].index(self.show_size.get())
        )

        # Output画面の比率を設定値に合わせる
        self.changeAreaSize(self.area_size.get())
        
        # ガイドの表示機能を反映する
        self.mode_change_show_guide()

        # 標準出力をログにリダイレクト
        self.switchStdoutDestination()

        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            try:
                self.locateCameraCmbbox()
                self.camera_id_entry.config(state='disable')
            except Exception as e:
                # Locate an entry instead whenever dll is not imported successfully
                self.camera_name_fromDLL.set("An error occurred when displaying the camera name in the Win/Mac environment.")
                self._logger.warning("An error occurred when displaying the camera name in the Win/Mac environment.")
                self._logger.warning(e)
                self.camera_name_cb.config(state='disable')
                self.camera_id_entry.config(state='normal')
            try:
                self.locateDeviceCmbbox()
                self.set_init_device_name()
            except Exception as e:
                self._logger.warning("An error occurred when checking serial device list.")
                self._logger.warning(e)
        elif platform.system() == 'Linux':
            self.camera_name_fromDLL.set("Linux environment. So that cannot show Camera name.")
            self.camera_name_cb.config(state='disable')
            self.use_keyboard_checkbox.config(state='disable')
            self.camera_id_entry.config(state='normal')
        else:
            self.camera_name_fromDLL.set("Unknown environment. Cannot show Camera name.")
            self.camera_name_cb.config(state='disable')
            self.use_keyboard_checkbox.config(state='disable')
            self.camera_id_entry.config(state='normal')
        # open up a camera
        self.camera = Camera(self.fps.get())
        self.openCamera()
        # activate serial communication
        try:
            self.locateDeviceCmbbox()
            self.set_init_device_name()
        except:
            self.serial_device_name_label.destroy()
            self.serial_device_name_cb.destroy()
            self.scan_device_button.destroy()
            self.com_port_entry["state"] = 'normal'
        
        if platform.system() == 'Windows' or platform.system() == "Darwin":
            pass
        else:
            self.com_port_entry["state"] = 'normal'

        self.ser = Sender.Sender(self.is_show_serial)
        self.activateSerial()
        self.activateKeyboard()
        self.preview = CaptureArea(self.camera,
                                   self.fps.get(),
                                   self.is_show_realtime,
                                #    self.ser,
                                   KeyPress(self.ser),
                                   self.camera_lf,
                                   *list(map(int, self.show_size.get().split("x")))
                                   )
        self.preview.config(cursor='crosshair')
        self.preview.grid(column='0', columnspan='7', row='2', padx='5', pady='5', sticky=tk.NSEW)
        self.loadCommands()

        # キャンバスに自動化スクリプトからアクセスできるようにする。
        Command.canvas = self.preview

        self.show_size_tmp = self.show_size_cb['values'].index(self.show_size_cb.get())
        self.root.bind('<Key-F5>', self.ReloadCommandWithF5)
        self._logger.debug("Bind F5 key to reload commands")
        self.root.bind('<Key-F6>', self.StartCommandWithF6)
        self._logger.debug("Bind F6 key to execute commands")
        self.root.bind('<Key-Escape>', self.StopCommandWithEsc)
        self._logger.debug("Bind Escape key to stop commands")

        # Main widget
        self.mainwindow = self.main_frame

        self.root.protocol("WM_DELETE_WINDOW", self.exit)
        self.preview.startCapture()

        self.menu = PokeController_Menubar(self)
        self.root.config(menu=self.menu)

        # logging.debug(f'python version: {sys.version}')

    def openCamera(self):
        self.camera.openCamera(self.camera_id.get())

    def assignCamera(self, event):
        if platform.system() != "Linux":
            self.camera_name_fromDLL.set(self.camera_dic[self.camera_id.get()])

    def locateCameraCmbbox(self):
        if platform.system() == 'Windows':
            try:
                import clr
                clr.AddReference(r"..\DirectShowLib\DirectShowLib-2005")
                from DirectShowLib import DsDevice, FilterCategory
                # Get names of detected camera devices
                captureDevices = DsDevice.GetDevicesOfCat(FilterCategory.VideoInputDevice)
                self.camera_dic = {cam_id: device.Name + " (" + device.DevicePath + ")" for cam_id, device in enumerate(captureDevices)}
            except:
                import device as dv
                captureDevices = dv.getDeviceList()
                self.camera_dic = {cam_id: device[0] for cam_id, device in enumerate(captureDevices)}
            
            self.camera_dic[str(max(list(self.camera_dic.keys())) + 1)] = 'Disable'
            self.camera_name_cb['values'] = ["No." + str(k) + ": " + v for k, v in self.camera_dic.items()]
            self._logger.debug(f"Camera list: {[device for device in self.camera_dic.values()]}")
            dev_num = len(self.camera_dic)
        elif platform.system() == "Darwin":
            cmd = 'system_profiler SPCameraDataType | grep "^    [^ ]" | sed "s/    //" | sed "s/://" '
            res = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
            # 出力結果の加工
            ret = res.stdout.decode('utf-8')
            cam_list = list(filter(lambda a: a != "", ret.split('\n')))
            self.camera_dic = {cam_id: camera_name for cam_id, camera_name in enumerate(cam_list)}
            dev_num = len(self.camera_name_cb['values'])
            self.camera_dic[str(max(list(self.camera_dic.keys())) + 1)] = 'Disable'
            self.camera_name_cb['values'] = ["No." + str(k) + ": " + v for k, v in self.camera_dic.items()]
        else:
            return False
        if self.camera_id.get() > dev_num - 1:
            print('Inappropriate camera ID! -> set to 0')
            self._logger.debug('Inappropriate camera ID! -> set to 0')
            self.camera_id.set(0)
            if dev_num == 0:
                print('No camera devices can be found.')
                self._logger.debug('No camera devices can be found.')

        #
        self.camera_id_entry.bind('<KeyRelease>', self.assignCamera)
        self.camera_name_cb.current(self.camera_id.get())

    def locateDeviceCmbbox(self):
        # ポート情報取得
        devices_description_list = []
        devices_list = list(list_ports.comports())        
        for d in devices_list:
            devices_description_list.append(d.description)
        self.serial_devices = sorted(devices_description_list, key=lambda s: int(re.search(r'COM(\d+)', s).groups()[0]))        
        self.serial_device_name_cb["values"] = self.serial_devices

    def saveCapture(self):
        self.camera.saveCapture()

    def OpenCaptureDir(self):
        directory = "Captures"
        self._logger.debug(f'Open folder: \'{directory}\'')
        if platform.system() == 'Windows':
            subprocess.call(f'explorer "{directory}"')
        elif platform.system() == 'Darwin':
            command = f'open "{directory}"'
            subprocess.run(command, shell=True)
    
    def sendLineImage(self):
        self.Line = Line_Notify()
        src = self.camera.readFrame()
        self.Line.send_message("***Manual****", src, 'token')

    def OpenCommandDir(self):
        if self.command_nb.index("current") == 1:
            directory = os.path.join("Commands", "McuCommands")
        else:
            directory = os.path.join("Commands", "PythonCommands")
        self._logger.debug(f'Open folder: \'{directory}\'')
        if platform.system() == 'Windows':
            subprocess.call(f'explorer "{directory}"')
        elif platform.system() == 'Darwin':
            command = f'open "{directory}"'
            subprocess.run(command, shell=True)

    def set_init_device_name(self):
        for d in self.serial_devices:
            if int(self.com_port.get()) == int(re.search(r'COM(\d+)', d).groups()[0]):
                self.serial_device_name.set(d)
                break
    
    def set_cameraid(self, event=None):
        keys = [k for k, v in self.camera_dic.items() if "No." + str(k) + ": " + v == self.camera_name_cb.get()]
        if keys:
            ret = keys[0]
        else:
            ret = None
        self.camera_id.set(ret)

    def set_device(self, event=None):
        self.com_port.set(int(re.search(r'COM(\d+)', self.serial_device_name.get()).groups()[0]))

    def applyFps(self, event=None):
        print('changed FPS to: ' + self.fps.get() + ' [fps]')
        self.preview.setFps(self.fps.get())

    def applyBaudRate(self, event=None):
        pass

    def applyWindowSize(self, event=None):
        width, height = map(int, self.show_size.get().split("x"))
        self.preview.setShowsize(height, width)
        if self.show_size_tmp != self.show_size_cb['values'].index(self.show_size_cb.get()):
            ret = tkmsg.askokcancel('確認', "この画面サイズに変更しますか？")
        else:
            return

        if ret:
            self.show_size_tmp = self.show_size_cb['values'].index(self.show_size_cb.get())
        else:
            self.show_size_cb.current(self.show_size_tmp)
            width_bef, height_bef = map(int, self.show_size.get().split("x"))
            self.preview.setShowsize(height_bef, width_bef)
            # self.show_size_tmp = self.show_size_cb['values'].index(self.show_size_cb.get())

    def activateSerial(self):
        if self.ser.isOpened():
            print('Port is already opened and being closed.')
            self.ser.closeSerial()
            self.keyPress = None
            self.activateSerial()
        else:
            if self.ser.openSerial(self.com_port.get(), self.com_port_name.get(), self.baud_rate.get()):
                print('COM Port ' + str(self.com_port.get()) + ' connected successfully')
                self._logger.debug('COM Port ' + str(self.com_port.get()) + ' connected successfully')
                self.keyPress = KeyPress(self.ser)
                self.settings.com_port.set(self.com_port.get())
                self.settings.baud_rate.set(self.baud_rate.get())
                self.settings.save()

    def inactivateSerial(self):
        if self.ser.isOpened():
            print('Port is already opened and being closed.')
            self.ser.closeSerial()
            self.keyPress = None

    def activateKeyboard(self):
        if self.is_use_keyboard.get():
            # enable Keyboard as controller
            if self.keyboard is None:
                self.keyboard = SwitchKeyboardController(self.keyPress)
                self.keyboard.listen()

            # bind focus
            if platform.system() != 'Linux':
                self.root.bind("<FocusIn>", self.onFocusInController)
                self.root.bind("<FocusOut>", self.onFocusOutController)

        else:
            if platform.system() != 'Linux':  # NOTE: Idk why but self.keyboard.stop() makes crash on Linux
                if self.keyboard is not None:
                    # stop listening to keyboard events
                    self.keyboard.stop()
                    self.keyboard = None

                self.root.bind("<FocusIn>", lambda _: None)
                self.root.bind("<FocusOut>", lambda _: None)

    def onFocusInController(self, event):
        # enable Keyboard as controller
        if event.widget == self.root and self.keyboard is None:
            self.keyboard = SwitchKeyboardController(self.keyPress)
            self.keyboard.listen()

    def onFocusOutController(self, event):
        # stop listening to keyboard events
        if event.widget == self.root and not self.keyboard is None:
            self.keyboard.stop()
            self.keyboard = None

    def createControllerWindow(self):
        if not self.controller is None:
            self.controller.focus_force()
            return

        window = ControllerGUI(self.root, self.ser)
        window.protocol("WM_DELETE_WINDOW", self.closingController)
        self.controller = window

    def activate_Left_stick_mouse(self):
        self.preview.ApplyLStickMouse()

    def activate_Right_stick_mouse(self):
        self.preview.ApplyRStickMouse()

    def mode_change_show_guide(self):
        Command.isGuide = self.is_show_guide.get()

    def mode_change_show_image(self):
        Command.isImage = self.is_show_image.get()

    # def createGetFromHomeWindow(self):
    #     if self.poke_treeview is not None:
    #         self.poke_treeview.focus_force()
    #         return
    #
    #     window2 = GetFromHomeGUI(self.root, self.settings.season, self.settings.is_SingleBattle)
    #     window2.protocol("WM_DELETE_WINDOW", self.closingGetFromHome)
    #     self.poke_treeview = window2

    def loadCommands(self):
        self.py_loader = CommandLoader(util.ospath('Commands/PythonCommands'),
                                       PythonCommandBase.PythonCommand)  # コマンドの読み込み
        self.mcu_loader = CommandLoader(util.ospath('Commands/McuCommands'), McuCommandBase.McuCommand)
        self.py_classes = self.py_loader.load()
        self.mcu_classes = self.mcu_loader.load()
        self.setCommandItems()
        self.assignCommand()

    def setCommandItems(self):
        self.py_cb['values'] = [c.NAME for c in self.py_classes]
        self.py_cb.current(0)
        self.mcu_cb['values'] = [c.NAME for c in self.mcu_classes]
        self.mcu_cb.current(0)

    def assignShortcutButton(self):
        self.assignCommand()
        if self.set_shortcut_num.get() == "(select)":
            print("not select num.")
        else:
            num = int(self.set_shortcut_num.get())
            self.shortcut_command_name[num] = self.cur_command.NAME
            
            if self.command_nb.index(self.command_nb.select()) == 0:
                self.shortcut_command_class[num] = "Python"
                
            elif self.command_nb.index(self.command_nb.select()) == 1:
                self.shortcut_command_class[num] = "Mcu"
            if num == 1:
                self.shortcut_1.set(self.shortcut_command_name[num][:8])
                self.shortcut_button_1_tooltip.text = self.shortcut_command_name[num]
            elif num == 2:
                self.shortcut_2.set(self.shortcut_command_name[num][:8])
                self.shortcut_button_2_tooltip.text = self.shortcut_command_name[num]
            elif num == 3:
                self.shortcut_3.set(self.shortcut_command_name[num][:8])
                self.shortcut_button_3_tooltip.text = self.shortcut_command_name[num]
            elif num == 4:
                self.shortcut_4.set(self.shortcut_command_name[num][:8])
                self.shortcut_button_4_tooltip.text = self.shortcut_command_name[num]
            elif num == 5:
                self.shortcut_5.set(self.shortcut_command_name[num][:8])
                self.shortcut_button_5_tooltip.text = self.shortcut_command_name[num]
            print()

    def assignCommand(self):
        # 選択されているコマンドを取得する
        self.mcu_cur_command = self.mcu_classes[self.mcu_cb.current()]()  # MCUコマンドについて

        # pythonコマンドは画像認識を使うかどうかで分岐している
        cmd_class = self.py_classes[self.py_cb.current()]
        if issubclass(cmd_class, PythonCommandBase.ImageProcPythonCommand):
            try:  # 画像認識の際に認識位置を表示する引数追加。互換性のため従来のはexceptに。
                self.py_cur_command = cmd_class(self.camera, self.preview)
            except TypeError:
                self.py_cur_command = cmd_class(self.camera)
            except:
                self.py_cur_command = cmd_class(self.camera)

        else:
            self.py_cur_command = cmd_class()

        if self.command_nb.index(self.command_nb.select()) == 0:
            self.cur_command = self.py_cur_command
        else:
            self.cur_command = self.mcu_cur_command

    def assignShortcutCommand(self, num):
        commandtype = self.shortcut_command_class[num]
        commandname = self.shortcut_command_name[num]
        commandindex = -1
        if commandtype in ["Python", "PYTHON", "python", "Py", "PY", "py"]:
            # ループを回してショートカットに割り当てられているpy_classのindexを探索する
            for i, name in enumerate(self.py_cb['values']):
                if name == commandname:
                    commandindex = i
                    break

            # cur_commnadにショートカットのコマンドを割り当てる。
            if commandindex == -1:
                print("shortcut Python command name error.")
                return False
            else:
                # pythonコマンドは画像認識を使うかどうかで分岐している
                cmd_class = self.py_classes[commandindex]
                if issubclass(cmd_class, PythonCommandBase.ImageProcPythonCommand):
                    try:  # 画像認識の際に認識位置を表示する引数追加。互換性のため従来のはexceptに。
                        self.py_cur_command = cmd_class(self.camera, self.preview)
                    except TypeError:
                        self.py_cur_command = cmd_class(self.camera)
                    except:
                        self.py_cur_command = cmd_class(self.camera)
                else:
                    self.py_cur_command = cmd_class()
                self.cur_command = self.py_cur_command
            return True
        elif commandtype in ["Mcu", "MCU", "mcu"]:
            # ループを回してショートカットに割り当てられているmcu_classのindexを探索する
            for i, name in enumerate(self.mcu_cb['values']):
                if name == commandname:
                    commandindex = i
                    break
            # cur_commnadにショートカットのコマンドを割り当てる。
            if commandindex == -1:
                print("shortcut Mcu command name error.")
                return False
            else:
                self.mcu_cur_command = self.mcu_classes[commandindex]()  # MCUコマンドについて
            self.cur_command = self.mcu_cur_command
            return True
        elif commandtype == "None":
            print(f"shortcut command ({num}) is not assigned.")
            return False
        else:
            print("shortcut command type error.")
            return False

    def controllButtons(self, event):
        note = event.widget
        if self.start_button["text"] == "Start":
            if note.tab(note.select(),"text") == "Shortcut":
                self.start_button["state"] = 'disabled'
                self.start_top_button["state"] = 'disabled'
            else:
                self.start_button["state"] = 'normal'
                self.start_top_button["state"] = 'normal'
        else:
            pass
        if note.tab(note.select(),"text") == "Shortcut":
            self.shortcut_set_button["state"] = 'disabled'
        else:
            self.shortcut_set_button["state"] = 'normal'
        
            

    def reloadCommands(self):
        # 表示しているタブを読み取って、どのコマンドを表示しているか取得、リロード後もそれが選択されるようにする
        oldval_mcu = self.mcu_cb.get()
        oldval_py = self.py_cb.get()

        self.py_classes = self.py_loader.reload()
        self.mcu_classes = self.mcu_loader.reload()

        # Restore the command selecting state if possible
        self.setCommandItems()
        if oldval_mcu in self.mcu_cb['values']:
            self.mcu_cb.set(oldval_mcu)
        if oldval_py in self.py_cb['values']:
            self.py_cb.set(oldval_py)
        self.assignCommand()
        print('Finished reloading command modules.')
        self._logger.info("Reloaded commands.")

    def pausePlay(self, *event):
        Command.isPause = True
        self.pause_button["text"] =  "Restart"
        self.pause_button["command"] = self.restartPlay
    
    def restartPlay(self, *event):
        Command.isPause = False
        self.pause_button["text"] =  "Pause"
        self.pause_button["command"] = self.pausePlay

    def startPlay(self, *event):
        if self.cur_command is None:
            print('No commands have been assigned yet.')
            self._logger.info('No commands have been assigned yet.')

        # set and init selected command
        self.assignCommand()

        print(self.start_button["text"] + ' ' + self.cur_command.NAME)
        self._logger.info(self.start_button["text"] + ' ' + self.cur_command.NAME)
        self.cur_command.start(self.ser, self.stopPlayPost)

        self.start_button["text"] = "Stop"
        self.start_top_button["text"] = "Stop"
        self.start_button["command"] = self.stopPlay
        self.start_top_button["command"] = self.stopPlay
        self.reload_command_button["state"] = 'disabled'
        self.shortcut_button_1["state"] = 'disabled'
        self.shortcut_button_2["state"] = 'disabled'
        self.shortcut_button_3["state"] = 'disabled'
        self.shortcut_button_4["state"] = 'disabled'
        self.shortcut_button_5["state"] = 'disabled'
        self.pause_button["state"] = 'normal'

    def startShortcutPlay(self, *event, num=0):
        if self.cur_command is None:
            print('No commands have been assigned yet.')
            self._logger.info('No commands have been assigned yet.')

        # set and init selected command
        flag = self.assignShortcutCommand(num)
        if flag:
            print(self.start_button["text"] + ' ' + self.cur_command.NAME)
            self._logger.info(self.start_button["text"] + ' ' + self.cur_command.NAME)
            self.cur_command.start(self.ser, self.stopPlayPost)

            self.start_button["text"] = "Stop"
            self.start_top_button["text"] = "Stop"
            self.start_button["command"] = self.stopPlay
            self.start_top_button["command"] = self.stopPlay
            self.start_button["state"] = 'normal'
            self.start_top_button["state"] = 'normal'
            self.reload_command_button["state"] = 'disabled'
            self.shortcut_button_1["state"] = 'disabled'
            self.shortcut_button_2["state"] = 'disabled'
            self.shortcut_button_3["state"] = 'disabled'
            self.shortcut_button_4["state"] = 'disabled'
            self.shortcut_button_5["state"] = 'disabled'
            self.pause_button["state"] = 'normal'
        else:
            pass

    def stopPlay(self):
        print(self.start_button["text"] + ' ' + self.cur_command.NAME)
        self._logger.info(self.start_button["text"] + ' ' + self.cur_command.NAME)
        self.start_button["state"] = 'disabled'
        self.start_top_button["state"] = 'disabled'
        
        Command.isPause = False
        self.pause_button["text"] =  "Pause"
        self.pause_button["command"] = self.pausePlay
        self.pause_button["state"] = "disable"

        self.cur_command.end(self.ser)

    def stopPlayPost(self):
        self.start_button["text"] = "Start"
        self.start_top_button["text"] = "Start"
        self.start_button["command"] = self.startPlay
        self.start_top_button["command"] = self.startPlay
        if (self.command_nb.index(self.command_nb.select())) == 2:
            self.start_button["state"] = "disable"
            self.start_top_button["state"] = "disable"
        else:
            self.start_button["state"] = 'normal'
            self.start_top_button["state"] = 'normal'
        self.reload_command_button["state"] = 'normal'
        self.shortcut_button_1["state"] = 'normal'
        self.shortcut_button_2["state"] = 'normal'
        self.shortcut_button_3["state"] = 'normal'
        self.shortcut_button_4["state"] = 'normal'
        self.shortcut_button_5["state"] = 'normal'

    def run(self):
        self._logger.debug("Start Poke-Controller")
        self.mainwindow.mainloop()

    def exit(self):

        ret = tkmsg.askyesno('確認', 'Poke Controllerを終了しますか？')
        if ret:
            if self.ser.isOpened():
                self.ser.closeSerial()
                print("Serial disconnected")
                # self._logger.info("Serial disconnected")

            # stop listening to keyboard events
            if not self.keyboard is None:
                self.keyboard.stop()
                self.keyboard = None

            # save settings
            self.settings.is_show_realtime.set(self.is_show_realtime.get())
            self.settings.is_show_guide.set(self.is_show_guide.get())
            self.settings.is_show_serial.set(self.is_show_serial.get())
            self.settings.is_use_keyboard.set(self.is_use_keyboard.get())
            self.settings.fps.set(self.fps.get())
            self.settings.show_size.set(self.show_size.get())
            self.settings.com_port.set(self.com_port.get())
            self.settings.baud_rate.set(self.baud_rate.get())
            self.settings.camera_id.set(self.camera_id.get())
            self.settings.command_class_1 = self.shortcut_command_class[1]
            self.settings.command_name_1.set(self.shortcut_command_name[1])
            self.settings.command_class_2 = self.shortcut_command_class[2]
            self.settings.command_name_2.set(self.shortcut_command_name[2])
            self.settings.command_class_3 = self.shortcut_command_class[3]
            self.settings.command_name_3.set(self.shortcut_command_name[3])
            self.settings.command_class_4 = self.shortcut_command_class[4]
            self.settings.command_name_4.set(self.shortcut_command_name[4])
            self.settings.command_class_5 = self.shortcut_command_class[5]
            self.settings.command_name_5.set(self.shortcut_command_name[5])
            self.settings.area_size = self.area_size.get()
            self.settings.stdout_destination = self.stdout_destination.get()

            self.settings.save()

            self.camera.destroy()
            cv2.destroyAllWindows()
            self._logger.debug("Stop Poke Controller")
            self.root.destroy()

    def closingController(self):
        self.controller.destroy()
        self.controller = None

    # def closingGetFromHome(self):
    #     self.poke_treeview.destroy()
    #     self.poke_treeview = None

    def loadSettings(self):
        self.settings = Settings.GuiSettings()
        self.settings.load()

    def ReloadCommandWithF5(self, *event):
        self.reloadCommands()

    def StartCommandWithF6(self, *event):
        if self.start_button["text"] == "Stop":
            print("Command is now working!")
            self._logger.debug("Command is now working!")
        elif self.start_button["text"] == "Start":
            self.startPlay()

    def StopCommandWithEsc(self, *event):
        if self.start_button["text"] == "Stop":
            self.stopPlay()

    def clearTextArea1(self):
        self.text_area_1.config(state='normal')
        self.text_area_1.delete('1.0', 'end')
        self.text_area_1.config(state='disable')

    def clearTextArea2(self):
        self.text_area_2.config(state='normal')
        self.text_area_2.delete('1.0', 'end')
        self.text_area_2.config(state='disable')

    def clearOutputs(self):
        self.clearTextArea1()
        self.clearTextArea2()
    
    def changeAreaSize(self, scale_value):
        text_area_1_size = int(float(scale_value))
        text_area_2_size = 40 - text_area_1_size
        self.text_area_1.config(height=text_area_1_size)
        self.text_area_2.config(height=text_area_2_size)

    def switchStdoutDestination(self):
        val = self.stdout_destination.get()
        if val == '1':
            sys.stdout = StdoutRedirector(self.text_area_1)
            print("standard output destination is switched.")
            Command.stdout_destination = val
        elif val == '2':
            sys.stdout = StdoutRedirector(self.text_area_2)
            print("standard output destination is switched.")
            Command.stdout_destination = val

# ToolTipのクラスは以下のサイトを参考に作成
# https://www.ishikawasekkei.com/index.php/2020/05/17/python-tkinter-gui-programing-tooltip/
class ToolTip:
    def __init__(self, widget, text="default tooltip"):
        self.widget = widget
        self.text = text
        self.widget.bind("<Motion>", self.moveCursor)
        self.widget.bind("<Leave>", self.leaveCursor)
        self.id = None
        self.tw = None
    
    def moveCursor(self, event):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)
        if not self.tw:
            id = self.id
            self.id = None
            if id:
                self.widget.after_cancel(id)
            self.id = self.widget.after(300, self.createTooltip)
    
    def leaveCursor(self, event):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)
        self.id = self.widget.after(300, self.destroyTooltip)
    
    def createTooltip(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)
        x, y = self.widget.winfo_pointerxy()
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.geometry(f"+{x+15}+{y-35}")
        label = tk.Label(self.tw, text=self.text, background="#98FB98",
                         relief="solid", borderwidth=0.5, justify="left")
        label.pack(ipadx=10)

    def destroyTooltip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()

class StdoutRedirector(object):
    """
    標準出力をtextウィジェットにリダイレクトするクラス
    重いので止めました →# update_idletasks()で出力のたびに随時更新(従来はfor loopのときなどにまとめて出力されることがあった)
    """

    def __init__(self, text_widget):
        self.text_space = text_widget

    def write(self, string):
        self.text_space.configure(state='normal')
        self.text_space.insert('end', string)
        self.text_space.see('end')
        # self.text_space.update_idletasks()
        self.text_space.configure(state='disabled')

    def flush(self):
        pass

if __name__ == '__main__':
    import tkinter as tk

    parser = argparse.ArgumentParser(description='Switch/GC automation support software using Python')
    parser.add_argument('--profile', '-p', help='profile', type=str, default='default')
    args = parser.parse_args()

    logger = PokeConLogger.root_logger()
    # logger.info('The root logger is created.')

    root = tk.Tk()
    app = PokeControllerApp(root, args.profile)
    app.run()