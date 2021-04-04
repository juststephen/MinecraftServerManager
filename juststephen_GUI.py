import tkinter as tk
from ctypes import windll
from PIL import Image, ImageTk
import webbrowser
import os
import sys

def _resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')

    return os.path.join(base_path, relative_path)

titlebar_colour = '#404040'
background_colour = '#2e2e2e'
optionsbar_colour = '#383838'
select_colour = '#484848'

_Default_Icon = _resource_path('DefaultIcon.ico')

_GWL_EXSTYLE=-20
_WS_EX_APPWINDOW=0x00040000
_WS_EX_TOOLWINDOW=0x00000080

_fullscreen_x, _fullscreen_y = 0, 0
WindowSize = (None, None)
Dragging = False
WindowCoords = (None, None)

def _set_appwindow(root):
    hwnd = windll.user32.GetParent(root.winfo_id())
    style = windll.user32.GetWindowLongPtrW(hwnd, _GWL_EXSTYLE)
    style = style & ~_WS_EX_TOOLWINDOW
    style = style | _WS_EX_APPWINDOW
    res = windll.user32.SetWindowLongPtrW(hwnd, _GWL_EXSTYLE, style)
    # re-assert the new window style
    root.wm_withdraw()
    root.after(10, lambda: root.wm_deiconify())

class AddTitleBar: # Adds a titlebar to the parentwindow
    def __init__(self, PARENTWINDOW, Title=None, Icon=None, Max=False, Min=False, Web=False, URL=None):
        self.PARENTWINDOW = PARENTWINDOW
        self.Title = Title
        if Icon is not None:
            self.Icon = _resource_path(Icon)
        else:
            self.Icon = _Default_Icon
        self.URL = URL

        self.PARENTWINDOW.overrideredirect(True)
        self.PARENTWINDOW.after(10, lambda: _set_appwindow(self.PARENTWINDOW))

        if self.Title is not None:
            self.PARENTWINDOW.title(self.Title)
        if self.Icon is not None:
            self.PARENTWINDOW.iconbitmap(self.Icon)

        self.TitleBar = tk.Frame(self.PARENTWINDOW, bg=titlebar_colour, bd=2)
        if self.Icon is not None:
            self.window_icon_img = ImageTk.PhotoImage(Image.open(self.Icon).resize((25,25)))
            self.TitleBar_Icon = tk.Label(self.TitleBar, image=self.window_icon_img, highlightthickness=0, bd=0)
        if self.Title is not None:
            self.TitleBar_Title = tk.Label(self.TitleBar, text=self.Title, bg=titlebar_colour, fg='white', bd=0)
        self.CloseButton = HoverButton(self.TitleBar,text='⨉',width=4,command=self.PARENTWINDOW.destroy,bg=titlebar_colour,activebackground='red',bd=0,font='bold',fg='white',highlightthickness=0,pady=3)
        if Max == True:
            self.MaxButton = HoverButton(self.TitleBar,text='🗖',width=4,command=lambda: self.MaximizeWindow('Button'),bg=titlebar_colour,activebackground='#606060',bd=0,font='bold',fg='white',highlightthickness=0,pady=3)
        if Min == True:
            self.MinButton = HoverButton(self.TitleBar,text='—',width=4,command=self.MinimizeWindow,bg=titlebar_colour,activebackground='#606060',bd=0,font='bold',fg='white',highlightthickness=0,pady=3)
        if Web == True:
            self.WebButton = HoverButton(self.TitleBar,text='🌐',width=4,command=self.WebBrowserOpen,bg=titlebar_colour,activebackground='#606060',bd=0,font='bold',fg='white',highlightthickness=0,pady=3)

        self.TitleBar.pack(fill=tk.X, side=tk.TOP)
        if self.Icon is not None:
            self.TitleBar_Icon.pack(side=tk.LEFT, padx=(0,8))
        if self.Title is not None:
            self.TitleBar_Title.pack(side=tk.LEFT)
        self.CloseButton.pack(side=tk.RIGHT)
        if Max == True:
            self.MaxButton.pack(side=tk.RIGHT)
        if Min == True:
            self.MinButton.pack(side=tk.RIGHT)
        if Web == True:
            self.WebButton.pack(side=tk.RIGHT)

    def MaximizeWindow(self, event=None):
        global _fullscreen_x
        global _fullscreen_y
        global WindowSize
        global WindowCoords
        if self.MaxButton.config()['text'][-1] == '🗖':
            WindowSize = (self.PARENTWINDOW.winfo_width(), self.PARENTWINDOW.winfo_height())
            WindowCoords = (self.PARENTWINDOW.winfo_x(), self.PARENTWINDOW.winfo_y())
            width, height = self.PARENTWINDOW.winfo_screenwidth(), self.PARENTWINDOW.winfo_screenheight()
            self.PARENTWINDOW.geometry(f'{width}x{height}+0+0')
            self.MaxButton.config(text='🗗')
            self.PARENTWINDOW.update()
            self.PARENTWINDOW.bind('<Configure>', lambda event: self.MaximizeWindow(event) if event.x != 0 or event.y != 0 else None)
            _fullscreen_x, _fullscreen_y = 0, 0
        elif Dragging or event == 'Button':
            self.PARENTWINDOW.bind('<Configure>', lambda event: _donothing())
            mouseoffset_x = int( self.PARENTWINDOW.winfo_pointerx() / self.PARENTWINDOW.winfo_screenwidth() * WindowSize[0] )
            if Dragging:
                _fullscreen_x = self.PARENTWINDOW.winfo_pointerx() - mouseoffset_x
                _fullscreen_y = self.PARENTWINDOW.winfo_pointery() - 8
            else: 
                _fullscreen_x, _fullscreen_y = WindowCoords[0], WindowCoords[1]
            self.PARENTWINDOW.geometry(f'{WindowSize[0]}x{WindowSize[1]}+{_fullscreen_x}+{_fullscreen_y}')
            if not Dragging:
                _fullscreen_x, _fullscreen_y = 0, 0
            self.PARENTWINDOW.update()
            self.MaxButton.config(text='🗖')

    def MinimizeWindow(self):
        hwnd = windll.user32.GetParent(self.PARENTWINDOW.winfo_id())
        self.PARENTWINDOW.update()
        windll.user32.CloseWindow(hwnd)

    def WebBrowserOpen(self):
        webbrowser.open(self.URL)

class HoverButton(tk.Label):
    def __init__(self, master, activebackground, command, index=None, **kw):
        tk.Label.__init__(self,master=master,**kw)
        self.defaultBackground = self["bg"]
        self.activebackground = activebackground
        self.command = command
        self.index = index
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<ButtonRelease-1>', self.pressed)

    def on_enter(self, event):
        self['bg'] = self.activebackground

    def on_leave(self, event):
        self['bg'] = self.defaultBackground
    
    def pressed(self, event):
        if 0 <= event.x <= self.winfo_width() and 0 <= event.y < self.winfo_height():
            if self.index is None:
                self.command()
            else:
                self.command(self.index)

class MoveWindow:
    def __init__(self, window, list_):
        self.window = window
        for self.MovableElement in list_:
            self.MovableElement.bind('<ButtonPress-1>', self.start_move)
            self.MovableElement.bind('<ButtonRelease-1>', self.stop_move)
            self.MovableElement.bind('<B1-Motion>', self.do_move)

    def start_move(self, event):
        global Dragging
        self.x = event.x
        self.y = event.y
        Dragging = True

    def stop_move(self, event):
        global _fullscreen_x
        global _fullscreen_y
        global Dragging
        self.x = None
        self.y = None
        _fullscreen_x, _fullscreen_y = 0, 0
        Dragging = False

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax + _fullscreen_x
        y = self.window.winfo_y() + deltay + _fullscreen_y
        self.window.geometry(f"+{x}+{y}")

def _donothing():
    pass

class MainWindow(tk.Frame):
    def __init__(self, PARENTWINDOW, Title=None, Icon=None, Max=False, Min=False, Web=False, URL=None):
        self.PARENTWINDOW = PARENTWINDOW
        self.main_window = AddTitleBar(PARENTWINDOW, Title=Title, Icon=Icon, Max=Max, Min=Min, Web=Web, URL=URL)
        self.DraggableList = [self.main_window.TitleBar, self.main_window.TitleBar_Icon]
        if Title is not None:
            self.DraggableList.append(self.main_window.TitleBar_Title)
        MoveWindow(self.PARENTWINDOW, self.DraggableList)

        tk.Frame.__init__(self, self.PARENTWINDOW, bg=background_colour, highlightthickness=0)
        self.pack(expand=1, fill=tk.BOTH)

class SyncLogin:
    def __init__(self, master):
        self.root = master
        self.SyncLoginWindow = tk.Toplevel(self.root)
        self.SyncLoginWindow.geometry('+825+256')
        self.SyncLogin_Window = AddTitleBar(self.SyncLoginWindow, 'Please Log In')
        self.SyncLoginWindow.grab_set() # User has to close the window before continuing
        MoveWindow(self.SyncLoginWindow, [self.SyncLogin_Window.TitleBar, self.SyncLogin_Window.TitleBar_Icon, self.SyncLogin_Window.TitleBar_Title])

        SyncLoginWindow_Frame = tk.Frame(self.SyncLoginWindow, bg=background_colour, bd=2)
        SyncLoginWindow_Frame.pack(expand=1, fill=tk.X)

        SyncLoginWindow_UsernameLabel = tk.Label(SyncLoginWindow_Frame, text='Username:', bg=background_colour, fg='white', bd=0)
        self.UsernameEntry = tk.Entry(SyncLoginWindow_Frame, bg=optionsbar_colour, fg='white', bd=2, relief=tk.FLAT)
        SyncLoginWindow_PasswordLabel = tk.Label(SyncLoginWindow_Frame, text='Password:', bg=background_colour, fg='white', bd=0)
        self.PasswordEntry = tk.Entry(SyncLoginWindow_Frame, show="•", bg=optionsbar_colour, fg='white', bd=2, relief=tk.FLAT)

        SyncLoginWindow_UsernameLabel.grid(row=0, column=0, sticky='w', padx=(10,5), pady=(10,5))
        self.UsernameEntry.grid(row=0, column=1, sticky='w', padx=(5,10), pady=(10,5))
        SyncLoginWindow_PasswordLabel.grid(row=1, column=0, sticky='w', padx=(10,5), pady=(5,10))
        self.PasswordEntry.grid(row=1, column=1, sticky='w', padx=(5,10), pady=(5,10))

        self.ButtonFrame = tk.Frame(self.SyncLoginWindow, bg=background_colour, bd=0)
        self.SyncLoginWindow_Success = tk.Label(self.ButtonFrame,text='',bg=background_colour,bd=2,fg='white',padx=5)

        self.ButtonFrame.pack(expand=1, fill=tk.X)
        self.SyncLoginWindow_Success.pack(side=tk.LEFT, padx=10, pady=(0,10))

class ConfirmationWindow:
    def __init__(self, master):
        self.root = master
        self.ConfirmWindow = tk.Toplevel(self.root)
        self.ConfirmWindow.geometry('+825+256')
        self.Confirm_Window = AddTitleBar(self.ConfirmWindow, 'Please Confirm')
        self.ConfirmWindow.grab_set() # User has to close the window before continuing
        MoveWindow(self.ConfirmWindow, [self.Confirm_Window.TitleBar, self.Confirm_Window.TitleBar_Icon, self.Confirm_Window.TitleBar_Title])

        self.TextLabel = tk.Label(self.ConfirmWindow, bg=background_colour, bd=2, fg='white', width=25, pady=10)
        self.TextLabel.pack(expand=1, fill=tk.X)

        self.ButtonFrame = tk.Frame(self.ConfirmWindow, bg=background_colour, bd=2, height=48)
        self.ButtonFrame.pack(expand=1, fill=tk.X)