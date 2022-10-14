import tkinter as tk
from re import search
from requests import get
from subprocess import Popen, PIPE, STDOUT
from tkinter import messagebox, filedialog


DPEDIT_URL = "https://github.com/programmer2514/DPEdit/releases/latest/download/DPEdit.exe"
UPDATE_URL = "https://raw.githubusercontent.com/programmer2514/DPEdit-GUI/main/dpedit_gui.py"
CURRENT_VERSION = "1.0.0"

monitor_positions = []
changes = []
is_applied = True
is_saved = False
profile_name = "default"

root = tk.Tk()
root.title('DPEdit GUI')
root.iconbitmap("dpedit.ico")


# Returns monitor position/size data in a list of tuples
def get_monitor_data():
    data = []
    proc = Popen(["DPEdit.exe", "/L"], shell=True, stdout=PIPE, stderr=PIPE)
    index = 0
    dims = [0, 0]

    # Check for errors
    for line in proc.stderr:
        if line:
            raise Exception("DPEdit failed to return monitor positions!")
    
    # Parse results into an ordered list of tuples
    # (index, width, height, x, y)
    for line in proc.stdout:
        dline = line.decode("utf-8")
        
        if "Display #" in dline:
            regex = search(r"([0-9]+)", dline)
            index = int(regex.group(1))

        if "Dimensions" in dline:
            regex = search(r"{([\-0-9]+), ([\-0-9]+)}", dline)
            dims = [int(regex.group(1)), int(regex.group(2))]
            
        if "Position" in dline:
            regex = search(r"{([\-0-9]+), ([\-0-9]+)}", dline)
            data.append((index, dims[0], dims[1], int(regex.group(1)), int(regex.group(2))))
            index = 0
            dims = [0, 0]

    return data


# Sets a monitor's position
def set_monitor_position(index, x, y):
    proc = Popen(["DPEdit.exe", str(index), str(x), str(y)], shell=True, stdout=PIPE, stderr=PIPE)

    # Check for errors
    for line in proc.stderr:
        if line:
            raise Exception("DPEdit failed to set monitor position!")
        
    # Check for handled errors or success
    for line in proc.stdout:
        dline = line.decode("utf-8")
        if "Skipping" in dline:
            raise Exception("DPEdit failed to set monitor position!")
        if "Done" in dline:
            return True

    # Fallback return
    return False


# Creates a new display profile
def new_profile(args=None):
    return


# Loads a saved display profile
def load_profile(args=None):
    return


# Saves the current display profile
def save_profile(args=None):
    return


# Saves the current display profile as a new file
def save_profile_as(args=None):
    return


# Undoes the last change
def undo_last(args=None):
    return


# Redoes the last change
def redo_last(args=None):
    return


# Applies all changes
def apply_changes(args=None):
    return


# Resets all changes since last apply
def reset_changes(args=None):
    return


# Shows info about the application
def about_app(args=None):
    return


# Shows all keyboard shortcuts
def keyboard_shortcuts(args=None):
    return


# Checks the application for updates
def check_for_updates(args=None):
    update_bin = False
    update_app = False

    # Check for DPEdit updates
    response_bin = get(DPEDIT_URL)
    try:
        file = open("DPEdit.exe", "rb")
        local_content = file.read()
        if (local_content != response_bin.content):
            update_bin = True
        file.close()
    except:
        update_bin = True

    # Check for application updates
    response_app = get(UPDATE_URL)
    try:
        file = open(__file__, "rb")
        local_content = file.read()
        if (local_content != response_app.content):
            update_app = True
        file.close()
    except:
        update_app = True

    # Update binaries if necessary
    if update_bin:
        if messagebox.askyesno(message="An update is available for the DPEdit binary.\nWould you like to install it now?", icon="question", title="Update"):
            with open("DPEdit.exe", "wb") as outfile:
                outfile.write(response_app.content)
            messagebox.showinfo(message="DPEdit binary updated successfully!", title="Success")

    # Update application if necessary
    if update_app:
        vnum = search(r"CURRENT_VERSION = \"([0-9.]+)\"", str(response_app.content)).group(1)
        if messagebox.askyesno(message="An update (v" + vnum + ") is available for DPEdit-GUI.\nWould you like to install it now?", icon="question", title="Update"):
            with open(__file__, "wb") as outfile:
                outfile.write(response_app.content)
            messagebox.showinfo(message="DPEdit-GUI has been updated successfully!\n The application will now restart to apply changes.", title="Success")
            Popen(__file__)
            root.destroy()


# Opens the DPEdit-GUI website
def open_website(args=None):
    return


# Saves and quits the application
def quit_app(args=None):
    return


# Main application code
if __name__ == "__main__":
    check_for_updates()
    # Initialize menus
    main_menu = tk.Menu(root)
    file_menu = tk.Menu(main_menu, tearoff="off")
    edit_menu = tk.Menu(main_menu, tearoff="off")
    help_menu = tk.Menu(main_menu, tearoff="off")

    # Add submenus to main menu
    main_menu.add_cascade(label="File", menu=file_menu, underline=0)
    main_menu.add_cascade(label="Edit", menu=edit_menu, underline=0)
    main_menu.add_cascade(label="Help", menu=help_menu, underline=0)

    # Add commands to file submenu
    file_menu.add_command(label="New Profile", underline=0, accelerator="Ctrl+N", command=new_profile)
    file_menu.add_command(label="Load Profile...", underline=0, accelerator="Ctrl+O", command=load_profile)
    file_menu.add_separator()
    file_menu.add_command(label="Save", underline=0, accelerator="Ctrl+S", command=save_profile)
    file_menu.add_command(label="Save As...", underline=0, accelerator="Ctrl+Shift+S", command=save_profile_as)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", underline=1, accelerator="Ctrl+Q", command=quit_app)

    # Add commands to edit submenu
    edit_menu.add_command(label="Undo", underline=0, accelerator="Ctrl+Z", command=undo_last)
    edit_menu.add_command(label="Redo", underline=0, accelerator="Ctrl+Y", command=redo_last)
    edit_menu.add_separator()
    edit_menu.add_command(label="Apply Changes", underline=0, accelerator="Ctrl+A", command=apply_changes)
    edit_menu.add_command(label="Reset Changes", underline=0, accelerator="Ctrl+R", command=reset_changes)

    # Add commands to help submenu
    help_menu.add_command(label="About DPEdit-GUI", underline=0, command=about_app)
    help_menu.add_separator()
    help_menu.add_command(label="Keyboard Shortcuts", underline=9, command=keyboard_shortcuts)
    help_menu.add_command(label="Check for Updates...", underline=10, command=check_for_updates)
    help_menu.add_command(label="Website", underline=0, command=open_website)
    
    # Add menus to root
    root.config(menu=main_menu)

    # Bind keyboard shortcuts
    root.bind('<Control-n>', new_profile)
    root.bind('<Control-o>', load_profile)
    root.bind('<Control-s>', save_profile)
    root.bind('<Control-S>', save_profile_as)
    root.bind('<Control-q>', quit_app)
    root.bind('<Control-z>', undo_last)
    root.bind('<Control-y>', redo_last)
    root.bind('<Control-a>', apply_changes)
    root.bind('<Control-r>', reset_changes)

    # Run program
    root.mainloop()
