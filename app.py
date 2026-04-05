import customtkinter as ctk
from index import Filesystem , DirectoryEntry

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.fs              = Filesystem()
        self.root_entry      = self.fs.init_root()
        self.selected_entry  = None
        self.selected_parent = None

        self.title("Inode Filesystem Emulator - Nero")
        self.geometry("1300x800")
        self.configure(fg_color="#0d1117")
        try:
            from PIL import Image, ImageTk
            img = Image.open("icon.ico")
            photo = ImageTk.PhotoImage(img)
            self.wm_iconphoto(True, photo)
            self._icon = photo  # keep reference so it doesn't get garbage collected
        except:
            pass

        self._build_ui()
        self._build_ui()
        self._refresh_tree()
        self.after(200, lambda: self.wm_iconbitmap("icon.ico"))  # ← add this
        self._refresh_tree()

    

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=4)
        self.grid_rowconfigure(0, weight=0)   # statsbar
        self.grid_rowconfigure(1, weight=1)   # main panels

        self._build_statusbar()
        self._build_left_panel()
        self._build_middle_panel()
        self._build_right_panel()


    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color="#161b22", height=32, corner_radius=0)
        bar.grid(row=1, column=0, columnspan=3, sticky="ew", padx=12, pady=(0,6))
        bar.grid_columnconfigure(0, weight=1)
        bar.grid_propagate(False)
        self.statsbar = ctk.CTkLabel(bar, text="",
                                     font=("Courier New", 10),
                                     text_color="#8b949e")
        self.statsbar.grid(row=0, column=0, padx=14)
        self._update_statsbar()

    def _update_statsbar(self):
        used_blocks  = sum(self.fs.block_bitmap)
        free_blocks  = 128 - used_blocks
        used_inodes  = len(self.fs.inodes)
        free_inodes  = 64 - used_inodes
        self.statsbar.configure(
            text=f"  Inodes: {used_inodes}/64 used  |  "
                 f"Blocks: {used_blocks}/128 used  ({free_blocks} free)  |  "
                 f"Block size: 512 bytes  |  "
                 f"Total disk: {128 * 512 // 1024} KB")



                                #   MIDDLE PANEL


    def _build_middle_panel(self):
        import tkinter.ttk as ttk

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=1, sticky="nsew", padx=3, pady=(0,12))
        frame.grid_rowconfigure(0, weight=3)
        frame.grid_rowconfigure(1, weight=2)
        frame.grid_columnconfigure(0, weight=1)

        # ── top: inode table ──
        top = ctk.CTkFrame(frame, fg_color="#161b22", corner_radius=10)
        top.grid(row=0, column=0, sticky="nsew", pady=(0,6))
        top.grid_rowconfigure(1, weight=1)
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top, text="Inode Table",
                     font=("Courier New", 13, "bold"),
                     text_color="#f0883e").grid(row=0, column=0, sticky="w",
                                                padx=14, pady=(14,6))

        style = ttk.Style()
        style.configure("IT.Treeview",
                        background="#1c2333",
                        foreground="#e6edf3",
                        fieldbackground="#1c2333",
                        borderwidth=0,
                        rowheight=24,
                        font=("Courier New", 10))
        style.configure("IT.Treeview.Heading",
                        background="#161b22",
                        foreground="#8b949e",
                        font=("Courier New", 9, "bold"))
        style.map("IT.Treeview",
                  background=[("selected", "#2a1f3d")],
                  foreground=[("selected", "#bc8cff")])
        style.layout("IT.Treeview",
                     [("IT.Treeview.treearea", {"sticky": "nswe"})])

        it_frame = ctk.CTkFrame(top, fg_color="#1c2333", corner_radius=8)
        it_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        it_frame.grid_rowconfigure(0, weight=1)
        it_frame.grid_columnconfigure(0, weight=1)

        cols = ("inode", "type", "name", "size", "perms", "links", "blocks")
        self.inode_tv = ttk.Treeview(it_frame, style="IT.Treeview",
                                     columns=cols, show="headings",
                                     selectmode="browse")

        headers = [
            ("Inode",  "inode",  52),
            ("T",      "type",   24),
            ("Name",   "name",  110),
            ("Size",   "size",   58),
            ("Perms",  "perms",  95),
            ("Links",  "links",  40),
            ("Blocks", "blocks", 46),
        ]
        for lbl, cid, w in headers:
            self.inode_tv.heading(cid, text=lbl)
            self.inode_tv.column(cid, width=w, anchor="center",
                                 stretch=(cid == "name"))

        self.inode_tv.grid(row=0, column=0, sticky="nsew")

        # ── bottom: block bitmap ──
        bot = ctk.CTkFrame(frame, fg_color="#161b22", corner_radius=10)
        bot.grid(row=1, column=0, sticky="nsew")
        bot.grid_rowconfigure(1, weight=1)
        bot.grid_columnconfigure(0, weight=1)

        hf = ctk.CTkFrame(bot, fg_color="transparent")
        hf.grid(row=0, column=0, sticky="ew", padx=14, pady=(14,6))
        ctk.CTkLabel(hf, text="Block Bitmap",
                     font=("Courier New", 13, "bold"),
                     text_color="#3fb950").pack(side="left")
        self.bitmap_stats = ctk.CTkLabel(hf, text="",
                     font=("Courier New", 10),
                     text_color="#8b949e")
        self.bitmap_stats.pack(side="right")

        import tkinter as tk
        canvas_wrap = ctk.CTkFrame(bot, fg_color="#1c2333", corner_radius=8)
        canvas_wrap.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))

        self.bitmap_canvas = tk.Canvas(canvas_wrap, bg="#1c2333",
                                       highlightthickness=0)
        self.bitmap_canvas.pack(fill="both", expand=True, padx=6, pady=6)
        self.bitmap_canvas.bind("<Configure>",
                                lambda e: self._refresh_bitmap())



                            
                                    #  RIGHT PANNEL



    def _build_right_panel(self):
        frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=10)
        frame.grid(row=1, column=2, sticky="nsew", padx=(6,12), pady=(0,12))
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Inode Inspector",
                     font=("Courier New", 13, "bold"),
                     text_color="#bc8cff").grid(row=0, column=0, columnspan=2,
                                                sticky="w", padx=14, pady=(14,10))

        # metadata fields
        self._insp = {}
        fields = [
            ("Inode #",     "inode_id"),
            ("Type",        "file_type"),
            ("Permissions", "perms"),
            ("Hard links",  "link_count"),
            ("Owner UID",   "uid"),
            ("Size",        "size"),
            ("Blocks used", "blocks"),
            ("Created",     "created"),
            ("Modified",    "modified"),
        ]
        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(frame, text=label + ":",
                         font=("Courier New", 10),
                         text_color="#8b949e",
                         anchor="e").grid(row=i+1, column=0,
                                          sticky="e", padx=(14,6), pady=3)
            var = ctk.StringVar(value="—")
            ctk.CTkLabel(frame, textvariable=var,
                         font=("Courier New", 10, "bold"),
                         text_color="#e6edf3",
                         anchor="w").grid(row=i+1, column=1,
                                          sticky="w", padx=(0,14), pady=3)
            self._insp[key] = var

        # separator
        sep = ctk.CTkFrame(frame, fg_color="#30363d", height=1)
        sep.grid(row=len(fields)+1, column=0, columnspan=2,
                 sticky="ew", padx=14, pady=(10,6))

        # block pointers section
        ctk.CTkLabel(frame, text="Block pointers:",
                     font=("Courier New", 10, "bold"),
                     text_color="#8b949e").grid(row=len(fields)+2, column=0,
                                                columnspan=2, sticky="w",
                                                padx=14, pady=(0,4))

        self.ptr_box = ctk.CTkTextbox(frame, height=80,
                                      font=("Courier New", 9),
                                      fg_color="#1c2333",
                                      text_color="#3fb950",
                                      corner_radius=6,
                                      state="disabled")
        self.ptr_box.grid(row=len(fields)+3, column=0, columnspan=2,
                          sticky="ew", padx=14, pady=(0,10))

        # separator
        sep2 = ctk.CTkFrame(frame, fg_color="#30363d", height=1)
        sep2.grid(row=len(fields)+4, column=0, columnspan=2,
                  sticky="ew", padx=14, pady=(0,8))

        # file content editor
        ctk.CTkLabel(frame, text="File Content:",
                     font=("Courier New", 10, "bold"),
                     text_color="#8b949e").grid(row=len(fields)+5, column=0,
                                                columnspan=2, sticky="w",
                                                padx=14, pady=(0,4))

        self.editor = ctk.CTkTextbox(frame, font=("Courier New", 11),
                                     fg_color="#1c2333",
                                     text_color="#e6edf3",
                                     corner_radius=6,
                                     state="disabled")
        self.editor.grid(row=len(fields)+6, column=0, columnspan=2,
                         sticky="nsew", padx=14, pady=(0,8))
        frame.grid_rowconfigure(len(fields)+6, weight=1)

        # save button
        self.save_btn = ctk.CTkButton(frame, text="💾  Save File",
                                      font=("Courier New", 11, "bold"),
                                      fg_color="#3fb950",
                                      hover_color="#2ea043",
                                      text_color="#ffffff",
                                      height=32, corner_radius=6,
                                      state="disabled",
                                      command=self._save_file)
        self.save_btn.grid(row=len(fields)+7, column=0, columnspan=2,
                           sticky="ew", padx=14, pady=(0,14))
    



                                 #LEFT PANNEL




    def _build_left_panel(self):
        # the outer frame
        frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=10)
        frame.grid(row=1, column=0, sticky="nsew", padx=(12,6), pady=(0,12))
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # title
        ctk.CTkLabel(frame, text="Directory Tree",
                     font=("Courier New", 13, "bold"),
                     text_color="#58a6ff").grid(row=0, column=0, sticky="w",
                                                padx=14, pady=(14,6))

        # the tree widget
        import tkinter.ttk as ttk

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Tree.Treeview",
                        background="#1c2333",
                        foreground="#e6edf3",
                        fieldbackground="#1c2333",
                        borderwidth=0,
                        rowheight=28,
                        font=("Courier New", 11))
        style.configure("Tree.Treeview.Heading",
                        background="#161b22",
                        foreground="#8b949e",
                        font=("Courier New", 10, "bold"))
        style.map("Tree.Treeview",
                  background=[("selected", "#1f3450")],
                  foreground=[("selected", "#58a6ff")])
        style.layout("Tree.Treeview",
                     [("Tree.Treeview.treearea", {"sticky": "nswe"})])

        tree_frame = ctk.CTkFrame(frame, fg_color="#1c2333", corner_radius=8)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, style="Tree.Treeview",
                                 columns=("inode", "type"),
                                 show="tree headings",
                                 selectmode="browse")
        self.tree.heading("#0",    text="Name")
        self.tree.heading("inode", text="Inode")
        self.tree.heading("type",  text="Type")
        self.tree.column("#0",    width=140, stretch=True)
        self.tree.column("inode", width=60,  anchor="center", stretch=False)
        self.tree.column("type",  width=55,  anchor="center", stretch=False)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(4,12))
        btn_frame.grid_columnconfigure((0,1), weight=1)

        ctk.CTkButton(btn_frame, text="+ File",
                      font=("Courier New", 11, "bold"),
                      fg_color="#58a6ff", hover_color="#388bfd",
                      text_color="#ffffff", height=30, corner_radius=6,
                      command=self._create_file).grid(row=0, column=0, padx=3, pady=3, sticky="ew")

        ctk.CTkButton(btn_frame, text="+ Folder",
                      font=("Courier New", 11, "bold"),
                      fg_color="#3fb950", hover_color="#2ea043",
                      text_color="#ffffff", height=30, corner_radius=6,
                      command=self._create_folder).grid(row=0, column=1, padx=3, pady=3, sticky="ew")

        ctk.CTkButton(btn_frame, text="⛓ Hard Link",
                      font=("Courier New", 11, "bold"),
                      fg_color="#bc8cff", hover_color="#8957e5",
                      text_color="#ffffff", height=30, corner_radius=6,
                      command=self._create_hard_link).grid(row=1, column=0, padx=3, pady=3, sticky="ew")

        ctk.CTkButton(btn_frame, text="✕ Delete",
                      font=("Courier New", 11, "bold"),
                      fg_color="#f85149", hover_color="#b91c1c",
                      text_color="#ffffff", height=30, corner_radius=6,
                      command=self._delete_selected).grid(row=1, column=1, padx=3, pady=3, sticky="ew")


    def _create_hard_link(self):
        from tkinter.simpledialog import askstring
        from tkinter import messagebox
        if not self.selected_entry:
            messagebox.showwarning("Warning", "Select a file first.")
            return
        inode = self.fs.inodes.get(self.selected_entry.inode_id)
        if not inode or inode.file_type == "directory":
            messagebox.showwarning("Warning", "Hard links only work on files, not folders.")
            return
        name = askstring("Hard Link", f"Link name for '{self.selected_entry.name}':")
        if not name:
            return
        parent = self._get_target_dir()
        try:
            self.fs.create_hard_link(self.selected_entry, parent, name.strip())
            self._refresh_tree()
            messagebox.showinfo("Hard Link Created",
                                f"'{name}' now points to inode #{self.selected_entry.inode_id}\n"
                                f"Link count is now: {inode.link_count}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        self._tree_map = {}
        self._fill_tree("", self.root_entry, None)
        root_id = self.tree.get_children()[0]
        self.tree.item(root_id, open=True)
        self._refresh_inode_table()
        self._refresh_bitmap()
        self._update_statsbar()

    def _fill_tree(self, parent_id, entry, parent_entry):
        inode = self.fs.inodes.get(entry.inode_id)
        if not inode:
            return
        icon = "📁" if inode.file_type == "directory" else "📄"
        tid  = self.tree.insert(parent_id, "end",
                                text=f"  {icon}  {entry.name}",
                                values=(f"#{inode.inode_id}", inode.file_type))
        self._tree_map[tid] = (entry, parent_entry)
        # auto expand every node
        self.tree.item(tid, open=True)
        for child in entry.children:
            self._fill_tree(tid, child, entry)


                                    #PLACE HOLDERS


    def _on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        tid = sel[0]
        entry, parent = self._tree_map.get(tid, (None, None))
        if not entry:
            return
        self.selected_entry  = entry
        self.selected_parent = parent
        inode = self.fs.inodes.get(entry.inode_id)
        if inode:
            self._update_inspector(inode)

    def _get_target_dir(self):
        # nothing selected — use root
        if not self.selected_entry:
            return self.root_entry

        inode = self.fs.inodes.get(self.selected_entry.inode_id)

        # selected a directory — create inside it
        if inode and inode.file_type == "directory":
            return self.selected_entry

        # selected a file — create next to it (same parent folder)
        if self.selected_parent:
            return self.selected_parent

        return self.root_entry

    def _create_file(self):
        from tkinter.simpledialog import askstring
        parent = self._get_target_dir()
        name   = askstring("New File", f"File name:")
        if not name:
            return
        try:
            self.fs.create_file(parent, name.strip())
            self._refresh_tree()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", str(e))

    def _create_folder(self):
        from tkinter.simpledialog import askstring
        parent = self._get_target_dir()
        name   = askstring("New Folder", f"Folder name:")
        if not name:
            return
        try:
            self.fs.create_directory(parent, name.strip())
            self._refresh_tree()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", str(e))

    def _delete_selected(self):
        from tkinter import messagebox
        if not self.selected_entry or not self.selected_parent:
            messagebox.showwarning("Warning", "Select a file or folder first.\nYou cannot delete root.")
            return
        name = self.selected_entry.name
        if not messagebox.askyesno("Confirm", f"Delete '{name}'?"):
            return
        try:
            self.fs.delete_entry(self.selected_parent, self.selected_entry)
            self.selected_entry  = None
            self.selected_parent = None
            self._refresh_tree()
        except Exception as e:
            messagebox.showerror("Error", str(e))

         
            #MIDDLE PANEL METHODES


    def _refresh_inode_table(self):
        self.inode_tv.delete(*self.inode_tv.get_children())
        for iid, inode in sorted(self.fs.inodes.items()):
            t    = "d" if inode.file_type == "directory" else "f"
            size = f"{inode.size}B"
            blks = len(inode.direct_blocks) + (
                   len(inode.indirect_block) if inode.indirect_block else 0)
            self.inode_tv.insert("", "end", values=(
                f"#{iid}", t, inode.name, size,
                inode.perm_string(), inode.link_count, blks))

    def _refresh_bitmap(self):
        import math
        c = self.bitmap_canvas
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10 or h < 10:
            return
        c.delete("all")
        cols    = 16
        rows    = math.ceil(128 / cols)
        pad     = 6
        cell_w  = (w - pad * 2) / cols
        cell_h  = (h - pad * 2) / rows
        for i, used in enumerate(self.fs.block_bitmap):
            col = i % cols
            row = i // cols
            x0  = pad + col * cell_w + 1
            y0  = pad + row * cell_h + 1
            x1  = x0 + cell_w - 3
            y1  = y0 + cell_h - 3
            color   = "#3fb950" if used else "#0d1117"
            outline = "#2ea043" if used else "#30363d"
            c.create_rectangle(x0, y0, x1, y1,
                               fill=color, outline=outline, width=0.5)
        used  = sum(self.fs.block_bitmap)
        total = 128
        self.bitmap_stats.configure(
            text=f"{used}/{total} used  ({100*used//total}%)")



                    #   RIGHT PANNEL METHODES


    def _update_inspector(self, inode):
        if not inode:
            for v in self._insp.values():
                v.set("—")
            self._set_ptr_text("")
            self.editor.configure(state="normal")
            self.editor.delete("1.0", "end")
            self.editor.configure(state="disabled")
            self.save_btn.configure(state="disabled")
            return

        self._insp["inode_id"].set(f"#{inode.inode_id}")
        self._insp["file_type"].set(inode.file_type)
        self._insp["perms"].set(inode.perm_string())
        self._insp["link_count"].set(str(inode.link_count))
        self._insp["uid"].set("1000")
        self._insp["size"].set(f"{inode.size} bytes")

        blocks = len(inode.direct_blocks) + (
                 len(inode.indirect_block) if inode.indirect_block else 0)
        self._insp["blocks"].set(str(blocks))
        self._insp["created"].set(inode.created.strftime("%Y-%m-%d %H:%M"))
        self._insp["modified"].set(inode.modified.strftime("%Y-%m-%d %H:%M"))

        # block pointers
        lines = []
        if inode.direct_blocks:
            lines.append(f"Direct:   {inode.direct_blocks}")
        if inode.indirect_block:
            lines.append(f"Indirect: {inode.indirect_block}")
        if not lines:
            lines = ["No blocks allocated yet."]
        self._set_ptr_text("\n".join(lines))

        # file content editor
        self.editor.configure(state="normal")
        self.editor.delete("1.0", "end")
        if inode.file_type == "file":
            self.editor.insert("1.0", inode.content)
            self.save_btn.configure(state="normal")
        else:
            self.editor.insert("1.0", "(directory — no content)")
            self.editor.configure(state="disabled")
            self.save_btn.configure(state="disabled")
            
    def _set_ptr_text(self, text):
        self.ptr_box.configure(state="normal")
        self.ptr_box.delete("1.0", "end")
        self.ptr_box.insert("1.0", text)
        self.ptr_box.configure(state="disabled")

    def _save_file(self):
        if not self.selected_entry:
            return
        inode = self.fs.inodes.get(self.selected_entry.inode_id)
        if not inode or inode.file_type != "file":
            return
        content = self.editor.get("1.0", "end-1c")
        self.fs._free_blocks(inode)
        inode.content  = content
        inode.size     = len(content.encode())
        inode.modified = __import__("datetime").datetime.now()
        direct, indirect     = self.fs._alloc_blocks(content)
        inode.direct_blocks  = direct
        inode.indirect_block = indirect
        self._update_inspector(inode)
        self._refresh_bitmap()
        self._refresh_inode_table()

if __name__ == "__main__":
    app = App()
    app.mainloop()