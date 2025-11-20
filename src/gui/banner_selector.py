import ttkbootstrap as ttk
from src.model.enum.patch_type import PatchType
from src.gui.helpers.build_character_name_string import build_character_name_string

class BannerSelector(ttk.Frame):
    def __init__(self, parent, patch_data, **kwargs):
        super().__init__(parent, **kwargs)

        self.patch_data = patch_data
        self.selections = {}

        self.col_widths = [45, 65, 125, 70, 45, 70]

        self._create_widget()


    def _create_widget(self):
        style = ttk.Style()
        style.configure("Selected.TFrame", background="#5b86fc")
        style.configure("Selected.TLabel", background="#5b86fc")
        style.configure("Selected.TCheckbutton", background="#5b86fc")

        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill="x", side="top")

        scroll_container = ttk.Frame(self)
        scroll_container.pack(fill="both", expand=True, side="top")

        self.canvas = ttk.Canvas(scroll_container, highlightthickness=0)

        scrollbar = ttk.Scrollbar(
            scroll_container,
            orient="vertical",
            command=self.canvas.yview,
            bootstyle="round"
        )

        self.scrollable_frame = ttk.Frame(self.canvas)

        canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        def on_canvas_configure(event):
            canvas_width = event.width
            self.canvas.itemconfig(canvas_frame, width=canvas_width)

        self.canvas.bind("<Configure>", on_canvas_configure)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self._create_header()
        self._create_rows()
        self._bind_mouse_scroll(self)


    def _create_header(self):
        headers = [
            " ",
            "Patch",
            "Character",
            "Awareness Lv.",
            "Weapon?",
            "Refinement Lv."
        ]

        for col, (text, width) in enumerate(zip(headers, self.col_widths)):
            label = ttk.Label(self.header_frame, text=text, anchor="center" if col in [0, 4] else "w")
            label.grid(row=0, column=col, padx=2, pady=(5, 2), sticky="ew")
            self.header_frame.grid_columnconfigure(col, minsize=width, uniform="col")


    def _create_rows(self):
        for col, width in enumerate(self.col_widths):
            self.scrollable_frame.grid_columnconfigure(col, minsize=width, uniform="col")

        for idx, patch in enumerate(self.patch_data.get("patches", []), start=0):
            self._create_patch_row(patch, idx)


    def _create_patch_row(self, patch, row_idx):
        patch_version = patch["version"]
        character = build_character_name_string(patch["featured_character"])

        row_frame = ttk.Frame(self.scrollable_frame)
        row_frame.grid(row=row_idx, column=0, columnspan=6, sticky="ew", padx=0, pady=1)

        for i, width in enumerate(self.col_widths):
            row_frame.grid_columnconfigure(i, minsize=width, uniform="col")

        if patch_version not in self.selections:
            self.selections[patch_version] = {
                "patch_type": patch["patch_type"],
                "pull_char": ttk.BooleanVar(value=False),
                "featured_character": patch["featured_character"],
                "awareness": ttk.StringVar(value="0"),
                "pull_weapon": ttk.BooleanVar(value=False),
                "refinement": ttk.StringVar(value="0"),
                "row_frame": row_frame
            }

        vars = self.selections[patch_version]

        vars["pull_char"].trace_add(
            "write",
            lambda *args, pv=patch_version: self._on_pull_char_changed(pv)
        )

        vars["awareness"].trace_add(
            "write",
            lambda *args, pv=patch_version: self._on_awareness_changed(pv)
        )

        vars["refinement"].trace_add(
            "write",
            lambda *args, pv=patch_version: self._on_refinement_changed(pv)
        )

        vars["pull_weapon"].trace_add(
            "write",
            lambda *args, pv=patch_version: self._on_weapon_changed(pv)
        )


        pull_check = ttk.Checkbutton(row_frame, variable=vars["pull_char"])
        pull_check.grid(row=0, column=0, padx=2, pady=1)


        patch_label_version_hint = "red" if PatchType(int(patch["patch_type"])) == PatchType.BIG else "white"
        patch_label = ttk.Label(row_frame, text=patch_version, foreground=patch_label_version_hint)
        patch_label.grid(row=0, column=1, padx=2, pady=1, sticky="w")

        char_label = ttk.Label(row_frame, text=character)
        char_label.grid(row=0, column=2, padx=2, pady=1, sticky="w")

        awareness_dropdown = ttk.Combobox(
            row_frame,
            textvariable=vars["awareness"],
            values=[str(i) for i in range(7)],
            state="readonly",
            width=12
        )
        awareness_dropdown.grid(row=0, column=3, padx=2, pady=1, sticky="w")
        awareness_dropdown.unbind_class("TCombobox", "<MouseWheel>")

        weapon_check = ttk.Checkbutton(row_frame, variable=vars["pull_weapon"])
        weapon_check.grid(row=0, column=4, padx=2, pady=1)

        refinement_dropdown = ttk.Combobox(
            row_frame,
            textvariable=vars["refinement"],
            values=[str(i) for i in range(7)],
            state="readonly",
            width=12
        )
        refinement_dropdown.grid(row=0, column=5, padx=2, pady=1, sticky="w")
        refinement_dropdown.unbind_class("TCombobox", "<MouseWheel>")


    def _on_pull_char_changed(self, patch_version):
        vars = self.selections[patch_version]
        is_selected = vars["pull_char"].get()

        if not is_selected:
            vars["pull_weapon"].set(False)

        row_frame = vars["row_frame"]

        if is_selected:
            row_frame.configure(style="Selected.TFrame")
            for widget in row_frame.winfo_children():
                widget_class = widget.winfo_class()
                if widget_class == "TLabel":
                    widget.configure(style="Selected.TLabel")
                elif widget_class == "TCheckbutton":
                    widget.configure(style="Selected.TCheckbutton")
        else:
            row_frame.configure(style="")
            for widget in row_frame.winfo_children():
                widget_class = widget.winfo_class()
                if widget_class == "TLabel":
                    widget.configure(style="TLabel")
                elif widget_class == "TCheckbutton":
                    widget.configure(style="TCheckbutton")


    def _on_awareness_changed(self, patch_version):
        vars = self.selections[patch_version]
        awareness_level = int(vars["awareness"].get())

        if awareness_level > 0:
            vars["pull_char"].set(True)


    def _on_refinement_changed(self, patch_version):
        vars = self.selections[patch_version]
        refinement_level = int(vars["refinement"].get())

        if refinement_level > 0:
            vars["pull_weapon"].set(True)


    def _on_weapon_changed(self, patch_version):
        vars = self.selections[patch_version]

        if vars["pull_weapon"].get():
            vars["pull_char"].set(True)


    def get_selections(self):
        result = {}

        for patch_version, vars in self.selections.items():
            result[patch_version] = {
                "patch_type": vars["patch_type"],
                "pull_char": vars["pull_char"].get(),
                "featured_character": vars["featured_character"],
                "awareness": int(vars["awareness"].get()),
                "pull_weapon": vars["pull_weapon"].get(),
                "refinement": int(vars["refinement"].get())
            }

        return result


    def set_selection(self, selections):
        for patch_version, data in selections.items():
            if patch_version in self.selections:
                vars = self.selections[patch_version]
                vars["pull_char"].set(data.get("pull_char", False))
                vars["awareness"].set(str(data.get("awareness", 0)))
                vars["pull_weapon"].set(data.get("pull_weapon", False))
                vars["refinement"].set(str(data.get("refinement", 0)))


    def get_selected_patches(self):
        return [
            version for version, data in self.get_selections().items()
            if data["pull_char"]
        ]


    def _bind_mouse_scroll(self, widget):
        widget.bind("<MouseWheel>", self._on_mouse_scroll)
        for child in widget.winfo_children():
            self._bind_mouse_scroll(child)


    def _on_mouse_scroll(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")