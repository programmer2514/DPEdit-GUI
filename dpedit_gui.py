import tkinter as tk
from re import search
from requests import get
from subprocess import Popen, PIPE, STDOUT
from tkinter import messagebox, filedialog



# Constants
# -------------
DPEDIT_URL = "https://github.com/programmer2514/DPEdit/releases/latest/download/DPEdit.exe"
UPDATE_URL = "https://raw.githubusercontent.com/programmer2514/DPEdit-GUI/main/dpedit_gui.py"
CURRENT_VERSION = "1.0.0"



# Display manager widget (extends tk.Frame)
# ---------------------------------------------
class DisplayManager(tk.Frame):
    
    # Initialize display manager
    # ------------------------------
    def __init__(self, parent):
        
        tk.Frame.__init__(self, parent)

        # Class globals
        self.drag_data = {"x": 0, "y": 0, "items": [None, None, None], "dragged": False}
        self.orig_view = [0, 0]
        self.selected_display = None
        self.prev_selected_display = None
        self.display_coords = []
        self.changes = []
        self.undoes = []
        self.ui_xy_vals = [tk.IntVar(self, value=0), tk.IntVar(self, value=0)]
        self.vcmd = (self.register(self.validate), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        # Create canvas
        self.canvas = tk.Canvas(self)
        self.canvas.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

        # Create sidebar top
        self.sidebar_top = tk.Frame(self)
        self.sidebar_top.pack(fill=tk.X, side=tk.TOP, anchor=tk.E)
        
        # Create header
        self.header = tk.Label(self.sidebar_top, text="No display selected", font=("Segoe UI", 20, "normal"), foreground="darkgrey")
        self.header.grid(row=0, column=0, padx=8, columnspan=2, sticky="n")

        # Create text boxes
        self.lbl_x = tk.Label(self.sidebar_top, text="X:", font=("Segoe UI", 14, "normal"), foreground="darkgrey")
        self.lbl_x.grid(row=1, column=0, padx=(12, 0), pady=4, sticky="nw")
        self.input_x = tk.Entry(self.sidebar_top, textvariable=self.ui_xy_vals[0], font=("Segoe UI", 12, "normal"), validate="key", validatecommand=self.vcmd, state=tk.DISABLED)
        self.input_x.grid(row=1, column=1, padx=(4, 32), pady=4, sticky="w")
        
        self.lbl_y = tk.Label(self.sidebar_top, text="Y:", font=("Segoe UI", 14, "normal"), foreground="darkgrey")
        self.lbl_y.grid(row=2, column=0, padx=(12, 0), pady=4, sticky="nw")
        self.input_y = tk.Entry(self.sidebar_top, textvariable=self.ui_xy_vals[1], font=("Segoe UI", 12, "normal"), validate="key", validatecommand=self.vcmd, state=tk.DISABLED)
        self.input_y.grid(row=2, column=1, padx=(4, 32), pady=4, sticky="w")

        # Create sidebar bottom
        self.sidebar_bottom = tk.Frame(self)
        self.sidebar_bottom.pack(fill=tk.X, side=tk.BOTTOM, anchor=tk.E)

        # Create buttons
        self.btn_apply = tk.Button(self.sidebar_bottom, text="Apply", command=self.apply, font=("Segoe UI", 12, "normal"), state=tk.DISABLED)
        self.btn_apply.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(2, 8))
        
        self.btn_reset = tk.Button(self.sidebar_bottom, text="Reset", command=self.reset, font=("Segoe UI", 12, "normal"), state=tk.DISABLED)
        self.btn_reset.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=2)

        # Place gridlines and displays
        self.draw_grid()
        self.enum_display_devices()

        # Bind textbox update events
        self.ui_xy_vals[0].trace_add('write', self.sync_entry)
        self.ui_xy_vals[1].trace_add('write', self.sync_entry)

        # Bind drag/click/resize events
        self.bind_drag_events(("draggable", "static", "disp_lbl", "prim_lbl"))
        self.canvas.tag_bind("grid", "<ButtonPress-1>", self.deselect)
        self.canvas.bind("<Configure>", self.resize)


    # Undo the last edit
    # ----------------------
    def undo(self):

        if len(self.changes) > 1:
            del self.display_coords

            # Copy current position to redo list and restore last position
            self.undoes.insert(0, [])
            self.display_coords = []
            for xy in self.changes[0]:
                self.undoes[0].append(xy.copy())
            for xy in self.changes[1]:
                self.display_coords.append(xy.copy())
        
            if len(self.undoes) > 50:
                del self.undoes[50:]
            
            self.deselect()
            del self.changes[0]
              
            # Update displays
            for display in self.display_data:
                for item in self.canvas.find_withtag(" " + str(display["index"]) + " "):
                    if "primary" in self.canvas.gettags(item) or "secondary" in self.canvas.gettags(item):
                        self.drag_data["items"][0] = item
                    if "disp_lbl" in self.canvas.gettags(item):
                        self.drag_data["items"][1] = item
                    if "prim_lbl" in self.canvas.gettags(item):
                        self.drag_data["items"][2] = item
                    
                diff_xy = ((self.display_coords[display["index"] - 1][0] // 10) - self.canvas.bbox(self.drag_data["items"][0])[0] - 1, (self.display_coords[display["index"] - 1][1] // 10) - self.canvas.bbox(self.drag_data["items"][0])[1] - 1)
                self.move_current_display(*diff_xy)

            # Find median point of all displays and shift canvas so they're centered
            self.canvas.xview_moveto(self.orig_view[0])
            self.canvas.yview_moveto(self.orig_view[1])
            
            x1, y1, x2, y2 = (*self.canvas.bbox(*self.canvas.find_withtag("fg")),)
            self._median_point = (x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2)
            
            self.canvas.scan_mark(self._median_point[0], self._median_point[1])
            self.canvas.scan_dragto(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, gain=1)
            
            # Clear drag data
            self.drag_data["items"][0] = None
            self.drag_data["items"][1] = None
            self.drag_data["items"][2] = None
            self.drag_data["dragged"] = False
            self.drag_data["x"] = 0
            self.drag_data["y"] = 0

            # Update sidebar data
            if len(self.changes) == 1:
                self.btn_reset.configure(state=tk.DISABLED)
                self.btn_apply.configure(state=tk.DISABLED)
            


    # Redo the last edit
    # ----------------------
    def redo(self):
        
        if len(self.undoes) > 0:
            del self.display_coords

            # Restore last undone position and update current position
            self.changes.insert(0, [])
            self.display_coords = []
            for xy in self.undoes[0]:
                self.changes[0].append(xy.copy())
                self.display_coords.append(xy.copy())
        
            if len(self.changes) > 50:
                del self.changes[50:]
            
            self.deselect()
            del self.undoes[0]
              
            # Update displays
            for display in self.display_data:
                for item in self.canvas.find_withtag(" " + str(display["index"]) + " "):
                    if "primary" in self.canvas.gettags(item) or "secondary" in self.canvas.gettags(item):
                        self.drag_data["items"][0] = item
                    if "disp_lbl" in self.canvas.gettags(item):
                        self.drag_data["items"][1] = item
                    if "prim_lbl" in self.canvas.gettags(item):
                        self.drag_data["items"][2] = item
                    
                diff_xy = ((self.display_coords[display["index"] - 1][0] // 10) - self.canvas.bbox(self.drag_data["items"][0])[0] - 1, (self.display_coords[display["index"] - 1][1] // 10) - self.canvas.bbox(self.drag_data["items"][0])[1] - 1)
                self.move_current_display(*diff_xy)

            # Find median point of all displays and shift canvas so they're centered
            self.canvas.xview_moveto(self.orig_view[0])
            self.canvas.yview_moveto(self.orig_view[1])
            
            x1, y1, x2, y2 = (*self.canvas.bbox(*self.canvas.find_withtag("fg")),)
            self._median_point = (x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2)
            
            self.canvas.scan_mark(self._median_point[0], self._median_point[1])
            self.canvas.scan_dragto(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, gain=1)
            
            # Clear drag data
            self.drag_data["items"][0] = None
            self.drag_data["items"][1] = None
            self.drag_data["items"][2] = None
            self.drag_data["dragged"] = False
            self.drag_data["x"] = 0
            self.drag_data["y"] = 0

            # Update sidebar data
            self.btn_reset.configure(state=tk.NORMAL)
            self.btn_apply.configure(state=tk.NORMAL)


    # Apply edits
    # ---------------
    def apply(self):

        if str(self.btn_apply['state']) == "normal":
            if messagebox.askyesno(message="Apply all changes?\nThis action cannot be undone", title="Apply"):

                success = True

                for i in range(len(self.display_coords)):
                    if not self.set_display_position(i + 1, self.display_coords[i][0], self.display_coords[i][1]):
                        success = False
                        break

                if success:
                    messagebox.showinfo(message="All changes applied successfully!", title="Success")

                self.display_data = self.get_display_data()
                self.reset(True)


    # Reset all edits since last apply
    # ------------------------------------
    def reset(self, skip_prompt = False):

        if str(self.btn_reset['state']) == "normal":
            if not skip_prompt:
                prompt = messagebox.askyesno(message="Reset all changes?\nThis action cannot be undone", title="Reset")
            else:
                prompt = True
            
            if prompt:
                
                del self.changes, self.display_coords, self.undoes
                self.changes = []
                self.undoes = []
                self.display_coords = []
                
                self.deselect()
                
                # Update displays
                for display in self.display_data:
                    for item in self.canvas.find_withtag(" " + str(display["index"]) + " "):
                        if "primary" in self.canvas.gettags(item) or "secondary" in self.canvas.gettags(item):
                            self.drag_data["items"][0] = item
                        if "disp_lbl" in self.canvas.gettags(item):
                            self.drag_data["items"][1] = item
                        if "prim_lbl" in self.canvas.gettags(item):
                            self.drag_data["items"][2] = item
                    
                    diff_xy = ((display["x"] // 10) - self.canvas.bbox(self.drag_data["items"][0])[0] - 1, (display["y"] // 10) - self.canvas.bbox(self.drag_data["items"][0])[1] - 1)
                    self.move_current_display(*diff_xy)
                    
                    self.display_coords.append([display["x"], display["y"]])

                # Update change list
                self.update_changelist()
                
                # Update sidebar data
                self.btn_reset.configure(state=tk.DISABLED)
                self.btn_apply.configure(state=tk.DISABLED)

                # Find median point of all displays and shift canvas so they're centered
                self.canvas.xview_moveto(self.orig_view[0])
                self.canvas.yview_moveto(self.orig_view[1])
                
                x1, y1, x2, y2 = (*self.canvas.bbox(*self.canvas.find_withtag("fg")),)
                self._median_point = (x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2)
                
                self.canvas.scan_mark(self._median_point[0], self._median_point[1])
                self.canvas.scan_dragto(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, gain=1)
                
                # Clear drag data
                self.drag_data["items"][0] = None
                self.drag_data["items"][1] = None
                self.drag_data["items"][2] = None
                self.drag_data["dragged"] = False
                self.drag_data["x"] = 0
                self.drag_data["y"] = 0


    # Sync canvas to display_coords
    # ---------------------------------
    def sync_canvas(self):

        del self.changes, self.undoes
        self.changes = []
        self.undoes = []

        self.update_changelist()
        self.deselect()
                
        # Update displays
        for display in self.display_data:
            for item in self.canvas.find_withtag(" " + str(display["index"]) + " "):
                if "primary" in self.canvas.gettags(item) or "secondary" in self.canvas.gettags(item):
                    self.drag_data["items"][0] = item
                if "disp_lbl" in self.canvas.gettags(item):
                    self.drag_data["items"][1] = item
                if "prim_lbl" in self.canvas.gettags(item):
                    self.drag_data["items"][2] = item
            
            diff_xy = ((self.display_coords[int(self.canvas.gettags(self.drag_data["items"][0])[0]) - 1][0] // 10) - self.canvas.bbox(self.drag_data["items"][0])[0] - 1, (self.display_coords[int(self.canvas.gettags(self.drag_data["items"][0])[0]) - 1][1] // 10) - self.canvas.bbox(self.drag_data["items"][0])[1] - 1)
            self.move_current_display(*diff_xy)

        # Find median point of all displays and shift canvas so they're centered
        self.canvas.xview_moveto(self.orig_view[0])
        self.canvas.yview_moveto(self.orig_view[1])
        
        x1, y1, x2, y2 = (*self.canvas.bbox(*self.canvas.find_withtag("fg")),)
        self._median_point = (x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2)
        
        self.canvas.scan_mark(self._median_point[0], self._median_point[1])
        self.canvas.scan_dragto(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, gain=1)
        
        # Clear drag data
        self.drag_data["items"][0] = None
        self.drag_data["items"][1] = None
        self.drag_data["items"][2] = None
        self.drag_data["dragged"] = False
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0


    # Update canvas to match entry fields
    # ---------------------------------------
    def sync_entry(self, var, index, mode):
        
        # If input is valid
        try:
            self.ui_xy_vals[0].get(), self.ui_xy_vals[1].get()
            if not self.drag_data["items"][0] and not "static" in self.canvas.gettags(self.selected_display):
                diff_xy = ((self.ui_xy_vals[0].get() // 10) - self.canvas.bbox(self.selected_display)[0] - 1, (self.ui_xy_vals[1].get() // 10) - self.canvas.bbox(self.selected_display)[1] - 1)
                
                # Find & move display and label
                self.canvas.move(self.selected_display, *diff_xy)
                for item in self.canvas.find_withtag(self.canvas.gettags(self.selected_display)[0]):
                    if "disp_lbl" in self.canvas.gettags(item) or "prim_lbl" in self.canvas.gettags(item):
                        self.canvas.move(item, *diff_xy)
                        
                # Set new display coords
                self.display_coords[int(self.canvas.gettags(self.selected_display)[0]) - 1][0] = self.ui_xy_vals[0].get()
                self.display_coords[int(self.canvas.gettags(self.selected_display)[0]) - 1][1] = self.ui_xy_vals[1].get()

                self.update_changelist()
            
                # Update sidebar data
                self.btn_reset.configure(state=tk.NORMAL)
                self.btn_apply.configure(state=tk.NORMAL)

                # Find median point of all displays and shift canvas so they're centered
                self.canvas.xview_moveto(self.orig_view[0])
                self.canvas.yview_moveto(self.orig_view[1])
                
                x1, y1, x2, y2 = (*self.canvas.bbox(*self.canvas.find_withtag("fg")),)
                self._median_point = (x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2)
                
                self.canvas.scan_mark(self._median_point[0], self._median_point[1])
                self.canvas.scan_dragto(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, gain=1)
        
        # Fallback for invalid inputs
        except:
            return


    # Update changelist and truncate if necessary
    # -----------------------------------------------
    def update_changelist(self):
        
        # This code is magic
        # Don't touch it unless you are an expert in pointers
        self.changes.insert(0, [])
        for xy in self.display_coords:
            self.changes[0].append(xy.copy())
        
        if len(self.changes) > 50:
            del self.changes[50:]


    # When a user starts dragging
    # -------------------------------
    def drag_start(self, event):
        
        self.prev_selected_display = self.selected_display

        # Get selected display
        for item in self.canvas.find_overlapping(self.canvas.canvasx(event.x) - 2, self.canvas.canvasy(event.y) - 2, self.canvas.canvasx(event.x) + 2, self.canvas.canvasy(event.y) + 2):
            if "draggable" in self.canvas.gettags(item) or "static" in self.canvas.gettags(item):
                self.selected_display = item

        # Update drag coords if applicable
        if "draggable" in self.canvas.gettags(self.selected_display):
            self.drag_data["items"][0] = self.selected_display
            for item in self.canvas.find_withtag(self.canvas.gettags(self.selected_display)[0]):
                if "disp_lbl" in self.canvas.gettags(item):
                    self.drag_data["items"][1] = item
                if "prim_lbl" in self.canvas.gettags(item):
                    self.drag_data["items"][2] = item
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

        self.update_selection()


    # When a user stops dragging
    # ------------------------------
    def drag_stop(self, event):
        
        # Check if any displays are overlapping and rearrange them until they don't
        if self.drag_data["items"][0] and self.drag_data["dragged"]:
            loop_iter = 0
            while True:
                loop_iter += 1
                for item in self.canvas.find_overlapping(self.canvas.bbox(self.drag_data["items"][0])[0] + 2,
                                                         self.canvas.bbox(self.drag_data["items"][0])[1] + 2,
                                                         self.canvas.bbox(self.drag_data["items"][0])[2] - 2,
                                                         self.canvas.bbox(self.drag_data["items"][0])[3] - 2):
                    if ("primary" in self.canvas.gettags(item) or "secondary" in self.canvas.gettags(item)) and item not in self.drag_data["items"]:
                        overlap_pos = self.canvas.bbox(item)
                        drag_pos = self.canvas.bbox(self.drag_data["items"][0])
                        overlap_med = (overlap_pos[0] + (overlap_pos[2] - overlap_pos[0]) // 2, overlap_pos[1] + (overlap_pos[3] - overlap_pos[1]) // 2)
                        drag_med = (drag_pos[0] + (drag_pos[2] - drag_pos[0]) // 2, drag_pos[1] + (drag_pos[3] - drag_pos[1]) // 2)
                        diff_xy = (drag_med[0] - overlap_med[0], drag_med[1] - overlap_med[1])
                        if max(abs(diff_xy[0]), abs(diff_xy[1])) == abs(diff_xy[0]):
                            if diff_xy[0] > 0:
                                self.move_current_display(overlap_pos[2] - drag_pos[0] - 2, 0)
                            else:
                                self.move_current_display(overlap_pos[0] - drag_pos[2] + 2, 0)
                        else:
                            if diff_xy[1] > 0:
                                self.move_current_display(0, overlap_pos[3] - drag_pos[1] - 2)
                            else:
                                self.move_current_display(0, overlap_pos[1] - drag_pos[3] + 2)
                    else:
                        loop_iter = -1

                # Prevent infinite looping
                # Might cause problems if you have 25+ monitors lol
                if loop_iter < 0 or loop_iter > 50:
                    break
                
            # Update display coords
            self.display_coords[int(self.canvas.gettags(self.drag_data["items"][0])[0]) - 1][0] = (self.canvas.bbox(self.drag_data["items"][0])[0] + 1) * 10
            self.display_coords[int(self.canvas.gettags(self.drag_data["items"][0])[0]) - 1][1] = (self.canvas.bbox(self.drag_data["items"][0])[1] + 1) * 10

            self.update_changelist()
            
            # Update sidebar data
            self.ui_xy_vals[0].set(self.display_coords[int(self.canvas.gettags(self.drag_data["items"][0])[0]) - 1][0])
            self.ui_xy_vals[1].set(self.display_coords[int(self.canvas.gettags(self.drag_data["items"][0])[0]) - 1][1])

            # Find median point of all displays and shift canvas so they're centered
            self.canvas.xview_moveto(self.orig_view[0])
            self.canvas.yview_moveto(self.orig_view[1])
            
            x1, y1, x2, y2 = (*self.canvas.bbox(*self.canvas.find_withtag("fg")),)
            self._median_point = (x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2)
            
            self.canvas.scan_mark(self._median_point[0], self._median_point[1])
            self.canvas.scan_dragto(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, gain=1)
                        
        # Clear drag data
        self.drag_data["items"][0] = None
        self.drag_data["items"][1] = None
        self.drag_data["items"][2] = None
        self.drag_data["dragged"] = False
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0


    # When a user drags
    # ---------------------
    def drag(self, event):
        
        # Get difference between current coords and new coords
        delta_x = event.x - self.drag_data["x"]
        delta_y = event.y - self.drag_data["y"]
        
        if abs(delta_x) > 3 or abs(delta_y) > 3 or self.drag_data["dragged"]:
        
            self.drag_data["dragged"] = True
            
            # Move display with mouse
            if self.drag_data["items"][0]:
                self.move_current_display(delta_x, delta_y)

                # Update display coords
                self.display_coords[int(self.canvas.gettags(self.drag_data["items"][0])[0]) - 1][0] = (self.canvas.bbox(self.drag_data["items"][0])[0] + 1) * 10
                self.display_coords[int(self.canvas.gettags(self.drag_data["items"][0])[0]) - 1][1] = (self.canvas.bbox(self.drag_data["items"][0])[1] + 1) * 10
                
                # Update sidebar data
                self.ui_xy_vals[0].set(self.display_coords[int(self.canvas.gettags(self.drag_data["items"][0])[0]) - 1][0])
                self.ui_xy_vals[1].set(self.display_coords[int(self.canvas.gettags(self.drag_data["items"][0])[0]) - 1][1])
                self.btn_reset.configure(state=tk.NORMAL)
                self.btn_apply.configure(state=tk.NORMAL)

            # Update current coords
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y


    # When the window is resized
    # ------------------------------
    def resize(self, event):

        # Find median point of all displays and shift canvas so they're centered
        self.canvas.xview_moveto(self.orig_view[0])
        self.canvas.yview_moveto(self.orig_view[1])
        
        x1, y1, x2, y2 = (*self.canvas.bbox(*self.canvas.find_withtag("fg")),)
        self._median_point = (x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2)
        
        self.canvas.scan_mark(self._median_point[0], self._median_point[1])
        self.canvas.scan_dragto(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, gain=1)


    # Deselect all displays
    # -------------------------
    def deselect(self, event=None):
        
        # Change monitor color to reflect selection
        if self.prev_selected_display:
            self.canvas.itemconfigure(self.prev_selected_display, outline="#2149c1", fill="#4169e1")
        self.canvas.itemconfigure(self.selected_display, outline="#2149c1", fill="#4169e1")
        
        # Update display selection
        self.prev_selected_display = self.selected_display
        self.selected_display = None
        
        # Update sidebar data
        self.header.configure(foreground="darkgrey", text="No display selected")
        self.lbl_x.configure(foreground="darkgrey")
        self.lbl_y.configure(foreground="darkgrey")
        self.input_x.configure(state=tk.DISABLED)
        self.input_y.configure(state=tk.DISABLED)
        self.ui_xy_vals[0].set(0)
        self.ui_xy_vals[1].set(0)


    # Move the currently selected display
    # ---------------------------------------
    def move_current_display(self, x_offset, y_offset):
        
        for i in range(3):
            self.canvas.move(self.drag_data["items"][i], x_offset, y_offset)


    # Move the currently selected display
    # ---------------------------------------
    def bind_drag_events(self, taglist):
        
        for tag in taglist:
            self.canvas.tag_bind(tag, "<ButtonPress-1>", self.drag_start)
            self.canvas.tag_bind(tag, "<ButtonRelease-1>", self.drag_stop)
            self.canvas.tag_bind(tag, "<B1-Motion>", self.drag)


    # Draw a grid on the canvas
    # -----------------------------
    def draw_grid(self):
        
        c = -4096
        
        # Place solid white background
        self.canvas.create_rectangle(-4096, -4096, 4096, 4096, fill="white", tags=("grid",))

        # Loop through from -4096 to 4096 and place gridlines
        for i in range(256):
            c += 32
            if c:
                self.canvas.create_line(-4096, c, 4096, c, fill="lightgrey", tags=("grid",))
                self.canvas.create_line(c, -4096, c, 4096, fill="lightgrey", tags=("grid",))

                # Place bold gridlines every other time
                if not c % 64:
                    self.canvas.create_line(-4096, c - 1, 4096, c - 1, fill="lightgrey", tags=("grid",))
                    self.canvas.create_line(c + 1, -4096, c + 1, 4096, fill="lightgrey", tags=("grid",))
                    self.canvas.create_line(-4096, c - 1, 4096, c - 1, fill="lightgrey", tags=("grid",))
                    self.canvas.create_line(c + 1, -4096, c + 1, 4096, fill="lightgrey", tags=("grid",))

        # Place dark gridlines as axes
        self.canvas.create_line(-4096, 0, 4096, 0, fill="darkgrey", tags=("grid",))
        self.canvas.create_line(0, -4096, 0, 4096, fill="darkgrey", tags=("grid",))
        self.canvas.create_line(-4096, -1, 4096, -1, fill="darkgrey", tags=("grid",))
        self.canvas.create_line(1, -4096, 1, 4096, fill="darkgrey", tags=("grid",))
        self.canvas.create_line(-4096, -1, 4096, -1, fill="darkgrey", tags=("grid",))
        self.canvas.create_line(1, -4096, 1, 4096, fill="darkgrey", tags=("grid",))


    # Update which display is currently selected
    # ----------------------------------------------
    def update_selection(self):
        
        # Change monitor color to reflect selection
        if self.prev_selected_display:
            self.canvas.itemconfigure(self.prev_selected_display, outline="#2149c1", fill="#4169e1")
        self.canvas.itemconfigure(self.selected_display, outline="#101961", fill="#113981")
        
        # Update sidebar data
        self.header.configure(foreground="black", text=("Display #" + str(int(self.canvas.gettags(self.selected_display)[0]))))
        self.lbl_x.configure(foreground="black")
        self.lbl_y.configure(foreground="black")
        self.input_x.configure(state=tk.NORMAL)
        self.input_y.configure(state=tk.NORMAL)
        self.ui_xy_vals[0].set(self.display_coords[int(self.canvas.gettags(self.selected_display)[0]) - 1][0])
        self.ui_xy_vals[1].set(self.display_coords[int(self.canvas.gettags(self.selected_display)[0]) - 1][1])


    # Validates text input
    # ------------------------
    def validate(self, action, index, value, prior_value, text, validation_type, trigger_type, widget_name):
        
        if value and value != "-":
            try:
                int(value)
                return True
            except ValueError:
                return False
        else:
            return True


    # Add a new display
    # ---------------------
    def create_display(self, x, y, w, h, taglist):
        
        x, y, w, h = x//10, y//10, w//10, h//10
        self.canvas.create_rectangle(x, y, x + w, y + h, outline="#2149c1", fill="#4169e1", tags=(*taglist, "fg"))
        self.canvas.create_text(x + w / 2, y + h / 2, text=taglist[0], anchor="center", font=("Segoe UI", 48, "normal"), fill="white", tags=(taglist[0], "disp_lbl", "fg"))
        self.canvas.create_text(x + w - 6, y - 6, text=("*" if "primary" in taglist else ""), anchor="ne", font=("Segoe UI", 24, "normal"), fill="white", tags=(taglist[0], "prim_lbl", "fg"))


    # Iterate through and insert all available displays
    # -----------------------------------------------------
    def enum_display_devices(self):
        
        self.display_data = self.get_display_data()

        # Initialize bounding rectangle coords with ridiculous values to be replaced
        x1, y1, x2, y2 = 1000000, 1000000, -1000000, -1000000

        # Find bounding rectangle
        for display in self.display_data:
            x1, y1, x2, y2 = min(x1, display["x"]), min(y1, display["y"]), max(x2, display["x"] + display["width"]), max(y2, display["y"] + display["height"])
        self._median_point = ((x1 + (x2 - x1) // 2) // 10, (y1 + (y2 - y1) // 2) // 10)
        
        # Insert displays
        for display in self.display_data:
            self.create_display(display["x"], display["y"], display["width"], display["height"], (" " + str(display["index"]) + " ", "primary" if display["primary"] else "secondary", "static" if display["primary"] else "draggable"))
            self.display_coords.append([display["x"], display["y"]])

        # Update change list
        self.update_changelist()

        # Set original view
        self.orig_view[0], self.orig_view[1] = self.canvas.xview()[0], self.canvas.yview()[0]

        # Pan canvas to center
        self.canvas.scan_mark(self._median_point[0], self._median_point[1])
        self.canvas.scan_dragto(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, gain=1)

        
    # Return display position/size data in a list of tuples
    # ---------------------------------------------------------
    def get_display_data(self):
        
        data = []
        proc = Popen(["DPEdit.exe", "/L"], shell=True, stdout=PIPE, stderr=PIPE)
        index = 0
        dims = [0, 0]

        # Check for errors
        for line in proc.stderr:
            if line:
                messagebox.showerror(message="DPEdit failed to get display position(s)!", title="Error")
        
        # Parse results into an ordered list of dictionaries
        for line in proc.stdout:
            dline = line.decode("utf-8")
            
            if "Display #" in dline:
                regex = search(r"([0-9]+)", dline)
                index = int(regex.group(1))
            
            if "Primary" in dline:
                regex = search(r"([0-9]+)", dline)
                primary = int(regex.group(1))

            if "Dimensions" in dline:
                regex = search(r"{([\-0-9]+), ([\-0-9]+)}", dline)
                dims = [int(regex.group(1)), int(regex.group(2))]
                
            if "Position" in dline:
                regex = search(r"{([\-0-9]+), ([\-0-9]+)}", dline)
                data.append({"index": index,
                             "primary": primary,
                             "width": dims[0],
                             "height": dims[1],
                             "x": int(regex.group(1)),
                             "y": int(regex.group(2))})
                index = 0
                dims = [0, 0]
                
        return data

        
    # Set a display's position
    # ----------------------------
    def set_display_position(self, index, x, y):
        
        proc = Popen(["DPEdit.exe", str(index), str(x), str(y)], shell=True, stdout=PIPE, stderr=PIPE)

        # Check for errors
        for line in proc.stderr:
            if line:
                messagebox.showerror(message="DPEdit failed to set display position!", title="Error")
                return False
            
        # Check for handled errors or success
        for line in proc.stdout:
            dline = line.decode("utf-8")
            if "Skipping" in dline:
                messagebox.showerror(message="DPEdit failed to set display position!", title="Error")
                return False
            if "Done" in dline:
                return True

        # Fallback message
        messagebox.showerror(message="DPEdit failed to set display position!", title="Error")
        return False



# Undo the last change
# ------------------------
def undo_last(args=None):
    disp_man.undo()


# Redo the last change
# ------------------------
def redo_last(args=None):
    disp_man.redo()


# Apply all changes
# ---------------------
def apply_changes(args=None):
    disp_man.apply()


# Reset all changes since last apply
# --------------------------------------
def reset_changes(args=None):
    disp_man.reset()


# Create a new display profile
# --------------------------------
def new_profile(args=None):
    disp_man.display_coords = [[0, 0], [1920, 1080]]
    disp_man.sync_canvas()
    return


# Load a saved display profile
# --------------------------------
def load_profile(args=None):
    return


# Save the current display profile
# ------------------------------------
def save_profile(args=None):
    return


# Save the current display profile as a new file
# --------------------------------------------------
def save_profile_as(args=None):
    file = filedialog.asksaveasfile(mode='w', initialdir="%userprofile%\documents", defaultextension=".dgc", initialfile='*', filetypes=(("DPEdit-GUI Config Files", "*.dgc"),("All Files", "*.*")))
    return


# Show info about the application
# -----------------------------------
def about_app(args=None):
    return


# Show all keyboard shortcuts
# -------------------------------
def keyboard_shortcuts(args=None):
    return


# Open the DPEdit-GUI website
# -------------------------------
def open_website(args=None):
    return


# Check the application for updates
# -------------------------------------
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
        if messagebox.askyesno(message="An update is available for the DPEdit binary.\nWould you like to install it now?", title="Update"):
            with open("DPEdit.exe", "wb") as outfile:
                outfile.write(response_app.content)
            messagebox.showinfo(message="DPEdit binary updated successfully!", title="Success")

    # Update application if necessary
    if update_app:
        vnum = search(r"CURRENT_VERSION = \"([0-9.]+)\"", str(response_app.content)).group(1)
        if messagebox.askyesno(message="An update (v" + vnum + ") is available for DPEdit-GUI.\nWould you like to install it now?", title="Update"):
            with open(__file__, "wb") as outfile:
                outfile.write(response_app.content)
            messagebox.showinfo(message="DPEdit-GUI has been updated successfully!\n The application will now restart to apply changes.", title="Success")
            Popen(__file__, shell=True)
            root.destroy()


# Save and quit the application
# ---------------------------------
def quit_app(args=None):
    root.destroy()



# Main application code
# -------------------------
if __name__ == "__main__":

    # Application globals
    is_saved = False
    profile_name = "default"

    # Initialize main window
    root = tk.Tk()
    root.title('DPEdit GUI')
    root.iconbitmap("dpedit.ico")
    root.geometry("900x500")
    
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

    disp_man = DisplayManager(root)
    
    disp_man.pack(expand=True, fill=tk.BOTH)

    # Run program
    root.mainloop()
