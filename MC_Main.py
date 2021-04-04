import juststephen_GUI
import tkinter as tk
import tkinter.ttk as ttk
from MC_Management import MC_Management, CompileServerJar
import base64
import os

LoginSuccess = False
Username, Password = None, None
ActiveFile = None

# Importing colors
background_colour = juststephen_GUI.background_colour
optionsbar_colour = juststephen_GUI.optionsbar_colour
select_colour = juststephen_GUI.select_colour

ButtonOptions = {'bg':optionsbar_colour, 'activebackground':select_colour, \
                 'bd':0, 'fg':'white', 'highlightthickness':0, 'padx':4, 'pady':4}

def _donothing():
    pass

def GetLoginDetailsSuccess(Buttons):   
    Buttons.SyncLoginWindow_Success.config(text='', fg='white')
    Buttons.SyncLoginWindow.destroy()

def CheckLogin():
    global LoginSuccess
    global Username
    global Password
    SyncLoginWindow_Button.command=_donothing
    Buttons.SyncLoginWindow.bind('<Return>', lambda event: _donothing())
    Username = base64.b64encode(Buttons.UsernameEntry.get().encode('utf-8'))
    Password = base64.b64encode(Buttons.PasswordEntry.get().encode('utf-8'))
    Buttons.SyncLoginWindow_Success.config(text='Loading...')
    Buttons.SyncLoginWindow_Success.update()
    if MC_Management('Login', Username, Password):
        LoginSuccess = True
        Buttons.SyncLoginWindow_Success.config(text='Success', fg='green')
        Buttons.SyncLoginWindow_Success.update()
        Buttons.SyncLoginWindow_Success.after(1000, lambda: GetLoginDetailsSuccess(Buttons))
    else:
        SyncLoginWindow_Button.command=CheckLogin
        Buttons.SyncLoginWindow.bind('<Return>', lambda event: CheckLogin())
        Buttons.SyncLoginWindow_Success.config(text='Failed', fg='red')
        Buttons.SyncLoginWindow_Success.update()
        Buttons.SyncLoginWindow_Success.after(2000, \
            lambda: Buttons.SyncLoginWindow_Success.config(text='', fg='white'))

def DoFunctionAfterConfirm(Action, Confirmation, File=None):
    Confirmation.ConfirmWindow.destroy()
    if File is not None:
        if Action == 'DownloadFile':
            MC_Management(Action, Username, Password, File=File, ProgressBar=ProgressBar, ProgressText=ProgressText)
            global ActiveFile
            ActiveFile = File
            EditText.delete(1.0, tk.END)
            Filename = ActiveFile.split('/')[-1]
            with open(f'files/{Filename}') as f:
                EditText.insert(1.0, f.read())
                f.close()
        elif Action == 'UploadFile':
            File = EditText.get(1.0, tk.END+'-1c').strip()
            Filename = ActiveFile.split('/')[-1]
            with open(f'files/{Filename}', 'w', encoding='utf-8') as f:
                f.write(File)
                f.close()
            MC_Management(Action, Username, Password, File=ActiveFile, ProgressBar=ProgressBar, ProgressText=ProgressText)     
    else:
        MC_Management(Action, Username, Password, File=File, ProgressBar=ProgressBar, ProgressText=ProgressText)
        ProgressText.config(text='Done', fg='green')
        ProgressText.update()
        ProgressText.after(1000, lambda: ProgressText.config(text='', fg='white'))
        ProgressText.update()

def ConfirmationWindow(Action, Text, File=None):
    Confirmation = juststephen_GUI.ConfirmationWindow(root)
    Confirmation.TextLabel.config(text=Text)
    ConfirmButton = juststephen_GUI.HoverButton(Confirmation.ButtonFrame, \
                    text='Confirm', **ButtonOptions, \
                    command=lambda: DoFunctionAfterConfirm(Action, Confirmation, File))
    CancelButton = juststephen_GUI.HoverButton(Confirmation.ButtonFrame, \
                    text='Cancel', **ButtonOptions, \
                    command=lambda: Confirmation.ConfirmWindow.destroy())
    ConfirmButton.place(relx=0.75, rely=0.5, anchor=tk.CENTER)
    CancelButton.place(relx=0.25, rely=0.5, anchor=tk.CENTER)
    Confirmation.ConfirmWindow.bind('<Return>', \
                    lambda event: DoFunctionAfterConfirm(Action, Confirmation, File))
    root.wait_window(Confirmation.ConfirmWindow)

def SaveFile():
    ConfirmationWindow('UploadFile', 'Save File?', File=ActiveFile)

def ReloadFile():    
    EditText.delete(1.0, tk.END)
    Filename = ActiveFile.split('/')[-1]
    with open(f'files/{Filename}') as f:
        EditText.insert(1.0, f.read())
        f.close()

def CloseFile():
    global ActiveFile
    ActiveFile = None
    EditText.delete(1.0, tk.END)


# GUI
root = tk.Tk()

main_window = juststephen_GUI.MainWindow(root, 'Minecraft Server Manager', 'DefaultIcon.ico', Min=True)
root.geometry('+600+200')

EditFrame = tk.Frame(main_window, bg=background_colour, bd=2)
EditButtonFrame = tk.Frame(main_window, bg=optionsbar_colour, bd=2)
StatusFrame = tk.Frame(main_window, bg=background_colour, bd=2, height=48)
ButtonFrame = tk.Frame(main_window, bg=optionsbar_colour, bd=2)

EditFrame.pack(expand=1, fill=tk.X)
EditButtonFrame.pack(expand=1, fill=tk.X)
StatusFrame.pack(expand=1, fill=tk.X)
ButtonFrame.pack(expand=1, fill=tk.X)


#### EditFrame ####
EditTextLabel = tk.Label(EditFrame, text='Edit File', bg=background_colour, fg='white', bd=0)
EditTextLabel.pack(pady=8)

EditTextScroll = tk.Scrollbar(EditFrame, bd=0)
EditTextScroll.pack(side=tk.RIGHT, expand=1, fill=tk.Y, pady=8, padx=(0, 8))

EditText = tk.Text(EditFrame, height=32, bg=optionsbar_colour, fg='white', bd=0, relief=tk.FLAT, font='TkDefaultFont', yscrollcommand = EditTextScroll.set)       
EditText.pack(side=tk.LEFT, expand=1, fill=tk.X, pady=8, padx=8)

EditTextScroll.config(command=EditText.yview)


#### EditButtonFrame ####
SaveButton = juststephen_GUI.HoverButton(EditButtonFrame, text='Save File', \
                    **ButtonOptions, command=SaveFile)
ReloadButton = juststephen_GUI.HoverButton(EditButtonFrame, text='Reload File', \
                    **ButtonOptions, command=ReloadFile)
ClearButton = juststephen_GUI.HoverButton(EditButtonFrame, text='Clear File', \
                    **ButtonOptions, command=lambda: EditText.delete(1.0, tk.END))
CloseButton = juststephen_GUI.HoverButton(EditButtonFrame, text='Close File', \
                    **ButtonOptions, command=CloseFile)
FolderButton = juststephen_GUI.HoverButton(EditButtonFrame, text='Open Folder', \
                    **ButtonOptions, command=lambda: os.startfile(f'{os.getcwd()}/files'))
CompileButton = juststephen_GUI.HoverButton(EditButtonFrame, text='Compile Server Jar', \
                    **ButtonOptions, command=lambda: CompileServerJar(ProgressText))
BackupButton = juststephen_GUI.HoverButton(EditButtonFrame, text='Backup World', \
                    **ButtonOptions, command=lambda: ConfirmationWindow('Backup', 'Make a backup of the world?'))

SaveButton.pack(side=tk.LEFT,padx=2)
ReloadButton.pack(side=tk.LEFT,padx=2)
ClearButton.pack(side=tk.LEFT,padx=2)
CloseButton.pack(side=tk.LEFT,padx=2)
FolderButton.pack(side=tk.RIGHT,padx=2)
CompileButton.pack(side=tk.RIGHT,padx=2)
BackupButton.pack(side=tk.RIGHT,padx=2)

#### StatusFrame ####
ProgressText = tk.Label(StatusFrame, bg=background_colour, bd=0, fg='white')
ProgressBar = ttk.Progressbar(StatusFrame, length=256, mode='determinate')

ProgressText.place(relx=0.75, rely=0.5, anchor=tk.CENTER)
ProgressBar.place(relx=0.25, rely=0.5, anchor=tk.CENTER)


#### ButtonFrame ####
UpdateButton = juststephen_GUI.HoverButton(ButtonFrame, text='Update Server', \
                    **ButtonOptions, command=lambda: ConfirmationWindow('Update', 'Update the server jar?'))
UpdatePlugginsButton = juststephen_GUI.HoverButton(ButtonFrame, text='Update Plugins', \
                    **ButtonOptions, command=lambda: ConfirmationWindow('UpdatePlugins', 'Update the plugins?'))
RestartButton = juststephen_GUI.HoverButton(ButtonFrame, text='Restart Server', \
                    **ButtonOptions, command=lambda: ConfirmationWindow('RestartServer', 'Restart the server?'))
EditPropertiesButton = juststephen_GUI.HoverButton(ButtonFrame, text='Edit server.properties', \
                    **ButtonOptions, command=lambda: ConfirmationWindow('DownloadFile', 'Edit server.properties?', 'server.properties'))
EditDynMarkersButton = juststephen_GUI.HoverButton(ButtonFrame, text='Edit Dynmap Markers', \
                    **ButtonOptions, command=lambda: ConfirmationWindow('DownloadFile', 'Edit Dynmap Markers?', 'plugins/dynmap/markers.yml'))
EditBlueMarkersButton = juststephen_GUI.HoverButton(ButtonFrame, text='Edit Bluemap Markers', \
                    **ButtonOptions, command=lambda: ConfirmationWindow('DownloadFile', 'Edit Bluemap Markers?', 'bluemap/web/data/markers.json'))

UpdateButton.pack(side=tk.LEFT,padx=2)
UpdatePlugginsButton.pack(side=tk.LEFT,padx=2)
RestartButton.pack(side=tk.LEFT,padx=2)
EditPropertiesButton.pack(side=tk.LEFT,padx=2)
EditDynMarkersButton.pack(side=tk.LEFT,padx=2)
EditBlueMarkersButton.pack(side=tk.LEFT,padx=2)


#### Startup Login ####
Buttons = juststephen_GUI.SyncLogin(root)
SyncLoginWindow_Button = juststephen_GUI.HoverButton(Buttons.ButtonFrame,text='Log In', \
                    **ButtonOptions, command=CheckLogin)
SyncLoginWindow_Button.pack(side=tk.RIGHT, padx=10, pady=(0,10))
Buttons.SyncLoginWindow.bind('<Return>', lambda event: CheckLogin())
root.wait_window(Buttons.SyncLoginWindow)

# Check if the login details are correct, if so lift root window, otherwise close it
if LoginSuccess:
    root.lift()
else:
    root.destroy()

root.mainloop()

Username, Password = None, None