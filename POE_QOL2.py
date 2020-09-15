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
import datetime

def click_item(a, b, c):
    """
    Used for when the user clicks on the highlight. Destroys the highlight and passes through the click action.
    Wish I knew how to make it 'click-through able'
    """
    exec(f"app.{a}.destroy()")
    x, y = pyautogui.position()
    pyautogui.click(x=x, y=y)  


def isRealWindow(hWnd):
    """Return True iff given window is a real Windows application window.
    Didn't write this; not sure its used -notaspy 14-9-2020
    """
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
    Didn't write this; not sure its used -notaspy 14-9-2020
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
        """
        This seems fine. -notaspy 14-9-2020
        """
        self.config = configparser.ConfigParser()
        self.config.read('setup.ini')
        super().__init__(master=master)

    def _create_ui(self):
        self.builder = builder = pygubu.Builder()
        builder.add_from_file('./buttons/Gui_Button_V1.ui')
        self.mainwindow = builder.get_object('Frame_1', self.master)
        self.font = font.Font(self.master, family="Times", size=20, weight="bold")
        builder.connect_callbacks(self)
        self.check_filter()  # This is legacy, to set the 
        #Note to self,  from trying a bunch of different resolutions and 3 monitors i found that,
        # stash/inv tabs had a fixed width to height ratio of 886/1440 (~0.6153)that must be obeyed.
        self.screen_res = [int(dim) for dim in self.config['Config']['screen_res'].split('x')]
        if len(self.screen_res) != 2:
            raise ValueError("Screen Resolution was not given correctly. Use no spaces and only a single 'x'.")
        # self.tab_width_frac = 888/1440 * self.screen_res[1] / self.screen_res[0] # Not actually used in the end.
        # from same experiments, stash starts 22 pixels away from edge, or 22/1440 fraction of screen width, and top is 215/1440 fraction.
        self.tab_origin = 22/1440 * self.screen_res[1], 215/1440 * self.screen_res[1]
        # apply similar rules to ending coordinates  -notaspy 14-9-2020
        self.tab_end = 864/1440 * self.screen_res[1], 1057/1440 * self.screen_res[1]
        # scale the size of a stash tab box depending on if it is quad or not.
        # TODO: currently set by user, but can actually get this from the site request
        if self.config['Config']['quad_tab'].lower() == 'true':
            box_density_scalar = 24
        else:
            box_density_scalar = 12
        # store the dimensions of an individual stash tab box (could be rectangular for some resolutions, so we store width and height)
        self.box_width = (self.tab_end[0] - self.tab_origin[0]) / (box_density_scalar)
        self.box_height = (self.tab_end[1] - self.tab_origin[1]) / (box_density_scalar)
        # Read the item filter text for the chaos recipe. This is used later for dynamically showing/hiding recipe items based on how many user has in tab
        self.default_filter_sections = self.read_default_chaos_filter_sections()
        # Store some meta-data about each item slot
        # Probably better to use another data-structure other than a list of dicts
        # scheme is [normalized width,
        # normalized height,
        # highlight color (can use any tk names color for now),
        # order user should add item to inventory to avoid inventory tetris fail situations,
        # threshold of how many items before dynamic filter editor starts to hide this item slot
        #]
        self.item_details = dict(
            Rings=[1, 1, 'green2', '4', int(self.config['Config']['threshold'])*2],
            OneHandWeapons=[1, 3, 'snow', '1', int(self.config['Config']['threshold']*2)],
            BodyArmours=[2, 3, 'snow', '1', int(self.config['Config']['threshold'])],
            Helmets=[2, 2, 'yellow', '2', int(self.config['Config']['threshold'])],
            Gloves=[2, 2, 'yellow', '2', int(self.config['Config']['threshold'])],
            Boots=[2, 2, 'yellow', '2', int(self.config['Config']['threshold'])],
            Belts=[2, 1, 'cyan', '3', int(self.config['Config']['threshold'])],
            Amulets=[1, 1, 'green2', '4', int(self.config['Config']['threshold'])],
            )
        # below is legacy code for when the screen resolution was hard-coded -notaspy 14-9-2020
        ## if self.config['Config']['screen_res'] == '1920x1080':
        ##     for win in getWindowSizes():
        ##         print(win)
        ##         if 'Path of Exile' in win[2]:
        ##             win32gui.SetWindowPos(win[0], win32con.HWND_NOTOPMOST, 0, 0, 1920, 1081, 0)
        
        # Here is where things start to get convoluted with me trying to re-do the algorithm. I'd like to streamline this.
        # I'll try to comment as best I can here and elsewhere

        # This is legacy, but works okay, so left it. stash_finder returns a dict of item slots and thier coordinates in the stash for unid'd and id'd items.
        # id'd items are basically ignored in this code, so not sure why they are tracked. Could be useful in future iterations.
        #TODO: Use data about identified items
        self.unident, self.ident = self.stash_finder()
        # Since the app has asynchronous knowledge of the items in tab, we want to have some local record. We'll call that latest_stash
        self.latest_stash = (self.unident.copy(), self.ident.copy())
        # initial dynamic filter update
        self.update_filter()
        # check if the local and remote inventories are synchronized. Uses the refresh rate (in seconds) set in the Setup.ini file.
        # I don't know the actual refresh rate of the website; seems random.
        # Probably fine to assume that the local record is most accurate for 60s since it should take about that long to vendor everything.
        self.check_inventory_sync()
        # Because of all the wonky `exec` calls, I am keeping track of the highlight overlay objects
        self.highlighted_items = []

    def run(self):
        """Run the main loop. Self explanatory."""
        self.mainwindow.mainloop()

    def chaos_recipe(self):
        """
        The meat of the program. Based on the number of complete sets, create top-level geometries that highlight areas of the screens for each item in the set.
        """
        # get a dictionary of the LOCAL complete sets items. 
        # this will be sync'd with the online stash if this is the first time this method has been called since last remote refresh
        # If user has clicked on a highlighted item, it gets removed locally, but the remote won't know that for a little.    
        # Dict keys are the slot name and values are the normalized positions.
        # the positions are lists of length-2 lists:eg [[x0, y0], [x1, y1]]
        unident = self.check_complete_set()

        # unident will be an empty dict if there's no complete sets left, and will inform user
        # TODO: This should work better
        if not unident:
            Msg.showinfo(title='POE QoL', message='Not enough Chaos Recipe Items')
        # if we have sets, go into the highlighting logic
        else:
            # if any previous highlights still exist, destroy them. 
            # If we don't do this, the way it is written below, if user doesn't manually click each highlight, they become non-interactive.
            # So, just killing everything is the fast and dirty way I decided wipe the screen clear if needed.
            if self.highlighted_items:
                for highlight in self.highlighted_items:
                    highlight.destroy()
            # loop through each item slot (key)
            for x in unident:
                # we will count from the top-left origin
                x_off = self.tab_origin[0]
                y_off = self.tab_origin[1]
                # cord_x, cord_y = self.unident[x].pop(0)  # Leaving this here so you can see the previous method was to pop items from the list. It was problematic. -notaspy 14-9-2020
                for i in range(len(unident[x]))
                    cord_x, cord_y = unident[x][0]
                    print(cord_y, self.box_height)
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
                    exec(f'self.highlighted_items.append(self.{x})')


                    if x not in ["Rings", "OneHandWeapons"]:
                            continue
                    # cord_x, cord_y = self.unident[x].pop(0)
                    # cord_x, cord_y = unident.pop(0)
                    print('199', unident)
                    cord_x, cord_y = unident[x][1]
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
                    exec(f'self.highlighted_items.append(self.{x2})')

    def check_inventory_sync(self):
        t_check = datetime.datetime.now()
        # if self.latest_stash[0] == self.unident or (t_check - self.last_update) < datetime.timedelta(seconds=float(self.config['Config']['refresh_time'])):
        if self.latest_stash[0] == self.unident and (t_check - self.last_update) < datetime.timedelta(seconds=float(self.config['Config']['refresh_time'])):
            self.synced = True
            for a in self.item_details.keys():
                try:
                    exec(f"app.{a}.destroy()")
                    exec(f"app.{a+'2'}.destroy()")
                except:
                    pass
        else:
            self.synced = False
        print(f"218 Synced?: {self.synced}")
        return self.synced

    def check_complete_set(self):
        if not self.check_inventory_sync():
            self.unident, self.ident = self.stash_finder()
            print(224, self.unident, self.ident)
            self.latest_stash = (self.unident, self.ident)
        try:
            self.unident
            self.latest_stash[0]
        except AttributeError:
            self.unident, self.ident = self.stash_finder()
            self.latest_stash[0] = (self.unident, self.ident)
        else:
            if len(self.latest_stash[0]["Rings"]) < 2 or len(self.latest_stash[0]['OneHandWeapons']) < 2:
                return False
            else:
                two_slot_max_sets = min((floor(len(self.latest_stash[0]["Rings"]) / 2), floor(len(self.latest_stash[0]["OneHandWeapons"]) / 2)))
                # print(two_slot_max_sets, 'tsms')
                one_slot_max_sets = min([len(self.latest_stash[0][_key]) for _key in self.latest_stash[0].keys() if _key not in ["Rings", "OneHandWeapons"]])
                # print(one_slot_max_sets, 'osms')
                ## Do we 
                max_sets = min((two_slot_max_sets, one_slot_max_sets, int(self.config['Config']['highlight_max_num_sets'])))
                # print(244, max_sets)
                if max_sets:
                    temp_unident = {_key:[] for _key in self.item_details.keys()}
                    # temp_unident = self.latest_stash[0].copy()
                    for key in self.item_details.keys():
                        # print(key)
                        if key in ["Rings", "OneHandWeapons"]:
                            _max_index = 2 * max_sets
                        else:
                            _max_index = max_sets
                        for i in range(_max_index):
                            temp_unident[key].append(self.latest_stash[0][key][i])

                    # self.unident = temp_unident
                    #TODO: Update the identified stash more often also!
                    # self.latest_stash[0] = temp_unident
                    return temp_unident
                else:
                    return False
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
        self.check_inventory_sync()
        if not self.synced:
            self.update_filter()

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
        self.last_update = datetime.datetime.now()
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
        #     self.change_filtering = 0
        #     for key, value in pos_last_unid.items():
        #         if key not in self.config['Config']['ignore_threshold']:
        #             tempvar = self.active_status[key]
        #             if len(value) >= int(self.config['Config']['threshold']) and tempvar[1][:4] == 'Show':
        #                 self.change_filtering = 1
        #                 self.active_status[key] = [tempvar[0], 'Hide\n']
        #             else:
        #                 if len(value) < int(self.config['Config']['threshold']):
        #                     if tempvar[1][:4] == 'Hide':
        #                         self.change_filtering = 1
        #                         self.active_status[key] = [tempvar[0], 'Show\n']
        #     else:
        #         if self.change_filtering == 1:
        #             self.filter_find()
                # return (pos_last_unid, pos_last_id)
            return (pos_last_unid, pos_last_id)

    def search(self, text):
        pyautogui.click(x=ceil(self.screen_res[0] * .1), y=ceil(self.screen_res[1] * .5))
        pyautogui.hotkey('ctrl', 'f')
        pyautogui.typewrite(text)

    def read_default_chaos_filter_sections(self):
        with open(self.config['Config']['default_filter'], 'r') as fil:
            chaos_filter = fil.readlines()
            section_lines_start_end = []
            section_starts = []
            for i, line in enumerate(chaos_filter):
                _line = line.lstrip()
                # print(len(_line))
                if len(_line) > 0 and _line[0] == "#":
                    # print(_line)
                    section_starts.append(i)
                    continue
            #print(section_starts)
            section_ends = [i for i in section_starts[1:]] + [len(chaos_filter)+1]
            #print(section_ends)
            sections = {}
            for i, j in zip(section_starts, section_ends):
                sections[chaos_filter[i].split(" ")[-1].rstrip()] = chaos_filter[i:j]
            # print("\n")
            # for s,v in sections.items():
                # print(s)
                # print(v)
                # print('\n')
        return sections


    def update_filter(self):
        with open(self.config['Config']['filter'], 'r') as fil:
            main_filter = fil.readlines()
            sections_start_line = 0
            sections_end_line = len(main_filter)
            for i, line in enumerate(fil.readlines()):
                # I use a random string to find where the chaos recipe section begins and ends
                if '234hn50987sd' in line:
                    sections_start_line = i + 1
                    continue
                elif '2345ina8dsf7' in line:
                    sections_end_line = i
                    break
                else:
                    Msg.showinfo(title='POE QoL', message='Cannot find the chaos recipe section in your main filter.\n' + 
                                                          'It should start with "# 234hn50987sd End Chaos Recipe Auto-Update Section" and end in "# 2345ina8dsf7 End Chaos Recipe Auto-Update Section".\n'+
                                                          'Msg @notaspy#6561 for help. 14-09-2020 \n')
                    # raise ValueError
                    return False
            # take everything before and after the chaos recipe section
            main_filter0 = main_filter[0:sections_start_line]
            main_filter1 = main_filter[sections_end_line:]
        sections_to_include = []
        for slot, details in self.item_details.items():
            try:
                print("\n456 LATEST STASH", self.latest_stash)
                print("\n457 LATEST STASH", slot, details)
                if len(self.latest_stash[0][slot]) < details[4]:  # if the number of items is greater than the threshold, keep it in the filter
                    self.default_filter_sections[slot][1] = "Show\n"
                else:
                    self.default_filter_sections[slot][1] = "Hide\n"
            except (AttributeError, ValueError):
                Msg.showinfo(title='POE QoL', message='Check default filter formatting. Msg @notaspy#6561 for help. 14-09-2020')
        new_filter_lines = [l for slt in self.default_filter_sections.values() for l in slt]
        print('\n', 464, new_filter_lines)
        new_main_filter = main_filter0 + new_filter_lines + main_filter1
        # with open(self.config['Config']['filter'], 'w') as fil:
        #     fil.write(new_main_filter)
        return True

    #Below are just methods that will search the stash tab for common things. didn't mess with these -notaspy 14-9-2020
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

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Path of Exile - Quality of Life (POE-QOL)')
    app = MyApplication(root)
    app.run()