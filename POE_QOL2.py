# decompyle3 version 3.3.2
# Python bytecode 3.8 (3413)
# Decompiled from: Python 3.8.5 (default, Sep  3 2020, 21:29:08) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: POE_QOL.py
import tkinter as tk
import tkinter.messagebox as Msg
import pygubu, pyautogui
from math import floor
import requests, json, configparser
from pygubu.builder import ttkstdwidgets
import os
from math import ceil
import win32con, win32gui
from tkinter import font


def click_item(a, b, c):
    exec(f"app.{a}.destroy()")
    x, y = pyautogui.position()
    # pyautogui.click(x=(b + 5), y=(c + 5))
    pyautogui.click(x=x, y=y)


def isRealWindow(hWnd):
    """Return True iff given window is a real Windows application window."""
    if not win32gui.IsWindowVisible(hWnd):
        return False
    if win32gui.GetParent(hWnd) != 0:
        return False
    hasNoOwner = win32gui.GetWindow(hWnd, win32con.GW_OWNER) == 0
    lExStyle = win32gui.GetWindowLong(hWnd, win32con.GWL_EXSTYLE)
    if not (lExStyle & win32con.WS_EX_TOOLWINDOW == 0 and hasNoOwner):
        if not (lExStyle & win32con.WS_EX_APPWINDOW != 0 and hasNoOwner):
            if win32gui.GetWindowText(hWnd):
                return True
        return False


def getWindowSizes():
    """
    Return a list of tuples (handler, (width, height)) for each real window.
    """

    def callback(hWnd, windows):
        if not isRealWindow(hWnd):
            return
        rect = win32gui.GetWindowRect(hWnd)
        windows.append((hWnd, (rect[2] - rect[0], rect[3] - rect[1]), win32gui.GetWindowText(hWnd)))

    windows = []
    win32gui.EnumWindows(callback, windows)
    return windows


class MyApplication(pygubu.TkApplication):

    def __init__(self, master=None):
        self.config = configparser.ConfigParser()
        self.config.read('setup.ini')
        super().__init__(master=master)

    def _create_ui(self):
        self.builder = builder = pygubu.Builder()
        builder.add_from_file('./buttons/Gui_Button_V1.ui')
        self.mainwindow = builder.get_object('Frame_1', self.master)
        self.font = font.Font(self.master, family="Times", size=20, weight="bold")
        builder.connect_callbacks(self)
        self.check_filter()
        #Note to self,  from trying a bunch of different resolutions,
        # stash/inv tabs had a fixed width to height ratio of 886/1440 (~0.6153)that must be obeyed
        self.screen_res = [int(dim) for dim in self.config['Config']['screen_res'].split('x')]
        if len(self.screen_res) != 2:
            raise ValueError("Screen Resolution was not given correctly. Use no spaces and only a single 'x'.")
        self.tab_width_frac = 888/1440 * self.screen_res[1] / self.screen_res[0]
        # from same experiments, stash starts 22 pixels away from edge, or 22/1440 fraction of screen width, and top is 215/1440 fraction
        self.tab_origin = 22/1440 * self.screen_res[1], 215/1440 * self.screen_res[1]
        # apply similar rules to ending coordinates
        self.tab_end = 864/1440 * self.screen_res[1], 1057/1440 * self.screen_res[1]
        if self.config['Config']['quad_tab'].lower() == 'true':
            box_density_scalar = 24
        else:
            box_density_scalar = 12
        self.box_width = (self.tab_end[0] - self.tab_origin[0]) / (box_density_scalar)
        self.box_height = (self.tab_end[1] - self.tab_origin[1]) / (box_density_scalar)
        self.item_details = dict(
            Rings=[1, 1, 'green2', '4'],
            OneHandWeapons=[1, 3, 'snow', '1'],
            BodyArmours=[2, 3, 'snow', '1'],
            Helmets=[2, 2, 'yellow', '2'],
            Gloves=[2, 2, 'yellow', '2'],
            Boots=[2, 2, 'yellow', '2'],
            Belts=[2, 1, 'cyan', '3'],
            Amulets=[1, 1, 'green2', '4'],
            )
        # if self.config['Config']['screen_res'] == '1920x1080':
        #     for win in getWindowSizes():
        #         print(win)
        #         if 'Path of Exile' in win[2]:
        #             win32gui.SetWindowPos(win[0], win32con.HWND_NOTOPMOST, 0, 0, 1920, 1081, 0)
        # self.latest_stash = None
        self.unident, self.ident = self.stash_finder()
        # self.latest_stash = (self.unident.copy(), self.ident.copy())

    def run(self):
        self.mainwindow.mainloop()

    def currency(self):
        self.search('"currency"')

    def essence(self):
        self.search('"essence of"')

    def divcard(self):
        self.search('"divination"')

    def fragment(self):
        self.search('"can be used in a personal Map device"')

    def splinter(self):
        self.search('"splinter"')

    def delve(self):
        self.search('"fossil"')

    def incubator(self):
        self.search('"incubator"')

    def map(self):
        self.search('"map""tier"')

    def blight_map(self):
        self.search('"blighted" "tier"')

    def veiled(self):
        self.search('"veiled"')

    def rare(self):
        self.search('"rare"')

    def unique(self):
        self.search('"unique"')

    def prophecy(self):
        self.search('"prophecy"')

    def gem(self):
        self.search('"gem"')

    def unid(self):
        self.search('"unid"')

    def chaos_recipe(self):
        if not self.check_complete_set():
            Msg.showinfo(title='POE QoL', message='Not enough Chaos Recipe Items')
        else:
            temp = []
            for x in self.unident:
                # if self.config['Config']['screen_res'] == '1920x1080':
                #     x_off = 18
                #     y_off = 163
                #     box_size = 26.3
                # elif self.config['Config']['screen_res'] == '1920x1018':
                #     x_off = 17
                #     y_off = 175
                #     box_size = 25
                # else:
                #     pass
                    # Msg.showinfo(title='POE QoL', message='Wrong Resolution msg: macr0s on Discord')
                x_off = self.tab_origin[0]
                y_off = self.tab_origin[1]
                cord_x, cord_y = self.unident[x].pop(0)
                cord_x = cord_x * self.box_width + x_off
                cord_y = cord_y * self.box_height + y_off
                box_width = self.box_width * self.item_details[x][0]
                box_height = self.box_height * self.item_details[x][1]
                exec(f"self.{x} = tk.Toplevel(self.mainwindow)")
                exec(f'self.{x}.attributes("-alpha", 0.65)')
                exec(f'self.{x}.config(background="{self.item_details[x][2]}")')
                exec(f"self.{x}.overrideredirect(1)")
                exec(f'self.{x}.attributes("-topmost", 1)')
                exec(f'self.{x}.geometry("{ceil(box_width)}x{ceil(box_height)}+{ceil(cord_x)}+{ceil(cord_y)}")')
                exec(f'self.{x}.bind("<Button-1>",lambda command, a=x,b=cord_x,c=cord_y: click_item(a,b,c))')

                if x not in ["Rings", "OneHandWeapons"]:
                        continue
                cord_x, cord_y = self.unident[x].pop(0)
                cord_x = cord_x * self.box_width + x_off
                cord_y = cord_y * self.box_height + y_off
                x2 = x + '2'
                exec(f"self.{x2} = tk.Toplevel(self.mainwindow)")
                exec(f"self.{x2}.attributes('-alpha', 0.65)")
                exec(f'self.{x2}.config(background="{self.item_details[x][2]}")')
                exec(f"self.{x2}.overrideredirect(1)")
                exec(f"self.{x2}.attributes('-topmost', 1)")
                exec(f"self.{x2}.geometry('{ceil(box_width)}x{ceil(box_height)}+{ceil(cord_x)}+{ceil(cord_y)}')")
                exec(f"self.{x2}.bind('<Button-1>',lambda event, a=x2,b=cord_x,c=cord_y: click_item(a,b,c))")


    # def check_inventory_sync(self):
    #     if self.latest_stash[0] != self.unident:
    #         self.unsynced = True
    #     else:
    #         self.unsynced = False

    def check_complete_set(self):
        try:
            self.unident
        except AttributeError:
            self.unident, self.ident = self.stash_finder()
        else:
            if len(self.unident["Rings"]) < 2 or len(self.unident['OneHandWeapons']) < 2:
                return False
            else:
                two_slot_max_sets = min((floor(len(self.unident["Rings"]) / 2), floor(len(self.unident["OneHandWeapons"]) / 2)))
                # print(two_slot_max_sets, 'tsms')
                one_slot_max_sets = min([len(self.unident[_key]) for _key in self.unident.keys() if _key not in ["Rings", "OneHandWeapons"]])
                # print(one_slot_max_sets, 'osms')
                ## Do we 
                max_sets = min((two_slot_max_sets, one_slot_max_sets, int(self.config['Config']['highlight_max_num_sets'])))
                # print(max_sets)
                if not max_sets:
                    return False
                else:
                    temp_unident = {_key:[] for _key in self.unident.keys()}
                    for key in self.unident.keys():
                        # print(key)
                        if key in ["Rings", "OneHandWeapons"]:
                            _max_index = 2 * max_sets
                        else:
                            _max_index = max_sets
                        for i in range(_max_index):
                            temp_unident[key].append(self.unident[key][i])
                    self.unident = temp_unident
                    return True
            # for key, value in self.unident.items():
            #     if key != 'Rings' or key != 'OneHandWeapons':
            #         print(key)
            #         if len(value) < 1:
            #             del self.unident
            #             del self.ident
            #             return False
            #     else:
            #         if len(value) < 2:
            #             del self.unident
            #             del self.ident
            #             return False
            # else:
            #     return True

    def show_chaos(self):
        self.builder2 = pygubu.Builder()
        self.builder2.add_from_file('./buttons/Gui_Button_V1.ui')
        self.top3 = tk.Toplevel(self.mainwindow)
        self.frame3 = self.builder2.get_object('Frame_2', self.top3)
        self.builder2.connect_callbacks(self)
        self.top3.overrideredirect(1)
        # if self.config['Config']['screen_res'] == '1920x1018':
        #     self.top3.geometry('+1180+900')
        # elif self.config['Config']['screen_res'] == '1920x1080':
        #     self.top3.geometry('+1180+940')
        # else:
        #     Msg.showinfo(title='POE QoL', message='Wrong Resolution msg: macr0s on Discord')
        self.top3.attributes('-topmost', 1)
        self.refresh_me()

    def close_overlay(self):
        self.top3.destroy()

    def refresh_me(self):
        unident, ident = self.stash_finder()
        for key, value in unident.items():
            alternative = len(ident.get(key, 0))
            exec(f'self.builder2.get_object("{key}").configure(text="{key[:4]}: {len(value)}/{alternative}")')

    def check_filter(self):
        rewrite = 0
        with open(self.config['Config']['filter'], 'r') as f:
            lines = f.readlines()
            if '# Chaos Recipe Ring' not in lines[0]:
                rewrite = 1
        if rewrite == 1:
            with open(self.config['Config']['filter'], 'w') as f:
                filterfile = open('filter')
                f.write(filterfile.read())
                filterfile.close()
                for line in lines:
                    f.writelines(line)

        self.active_status = {'Rings':[1, lines[1]],
                            'Belts':[15, lines[15]],
                            'Amulets':[28, lines[28]],
                            'Boots':[41, lines[41]],
                            'Gloves':[55, lines[55]],
                            'Helmets':[69, lines[69]],
                            'BodyArmours':[83, lines[83]],
                            'OneHandWeapons':[97, lines[97]]
                            }

    def stash_finder(self):
        pos_last_unid = {'BodyArmours':[],  'Helmets':[],  'OneHandWeapons':[],  'Gloves':[],  'Boots':[],  'Amulets':[],  'Belts':[],  'Rings':[]}
        pos_last_id = {'BodyArmours':[],  'Helmets':[],  'OneHandWeapons':[],  'Gloves':[],  'Boots':[],  'Amulets':[],  'Belts':[],  'Rings':[]}
        stash_tab = f"https://www.pathofexile.com/character-window/get-stash-items?league={self.config['Config']['league']}&tabIndex={self.config['Config']['tab']}&accountName={self.config['Config']['account']}"
        a = requests.get(stash_tab, cookies=dict(POESESSID=(self.config['Config']['POESESSID'])))
        for x in json.loads(a.text)['items']:
            if x['name'] == '' and x['frameType'] != 3:
                if 'BodyArmours' in x['icon']:
                    pos_last_unid['BodyArmours'].append([x['x'], x['y']])
                elif 'Helmets' in x['icon']:
                    pos_last_unid['Helmets'].append([x['x'], x['y']])
                elif 'OneHandWeapons' in x['icon']:
                    pos_last_unid['OneHandWeapons'].append([x['x'], x['y']])
                elif 'Gloves' in x['icon']:
                    pos_last_unid['Gloves'].append([x['x'], x['y']])
                elif 'Boots' in x['icon']:
                    pos_last_unid['Boots'].append([x['x'], x['y']])
                elif 'Amulets' in x['icon']:
                    pos_last_unid['Amulets'].append([x['x'], x['y']])
                elif 'Belts' in x['icon']:
                    pos_last_unid['Belts'].append([x['x'], x['y']])
                elif 'Rings' in x['icon']:
                    pos_last_unid['Rings'].append([x['x'], x['y']])
            else:
                if x['frameType'] == 3:
                    pass
                else:
                    if 'BodyArmours' in x['icon']:
                        pos_last_id['BodyArmours'].append([x['x'], x['y']])
                    else:
                        if 'Helmets' in x['icon']:
                            pos_last_id['Helmets'].append([x['x'], x['y']])
                        else:
                            if 'OneHandWeapons' in x['icon']:
                                pos_last_id['OneHandWeapons'].append([x['x'], x['y']])
                            else:
                                if 'Gloves' in x['icon']:
                                    pos_last_id['Gloves'].append([x['x'], x['y']])
                                else:
                                    if 'Boots' in x['icon']:
                                        pos_last_id['Boots'].append([x['x'], x['y']])
                                    else:
                                        if 'Amulets' in x['icon']:
                                            pos_last_id['Amulets'].append([x['x'], x['y']])
                                        else:
                                            if 'Belts' in x['icon']:
                                                pos_last_id['Belts'].append([x['x'], x['y']])
                                            else:
                                                if 'Rings' in x['icon']:
                                                    pos_last_id['Rings'].append([x['x'], x['y']])
        else:
            self.change_filtering = 0
            for key, value in pos_last_unid.items():
                if key not in self.config['Config']['ignore_threshold']:
                    tempvar = self.active_status[key]
                    if len(value) >= int(self.config['Config']['threshold']) and tempvar[1][:4] == 'Show':
                        self.change_filtering = 1
                        self.active_status[key] = [tempvar[0], 'Hide\n']
                    else:
                        if len(value) < int(self.config['Config']['threshold']):
                            if tempvar[1][:4] == 'Hide':
                                self.change_filtering = 1
                                self.active_status[key] = [tempvar[0], 'Show\n']
            else:
                if self.change_filtering == 1:
                    self.filter_find()
                return (pos_last_unid, pos_last_id)

    def search(self, text):
        pyautogui.click(x=97, y=86)
        pyautogui.hotkey('ctrl', 'f')
        pyautogui.typewrite(text)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Path of Exile - Quality of Life (POE-QOL)')
    app = MyApplication(root)
    app.run()