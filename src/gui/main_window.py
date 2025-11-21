import json
import threading
import pywinstyles
import ttkbootstrap as ttk
import src.gui.helpers.validators as validators
from tkinter import PhotoImage, messagebox
from src.core.simulator import Simulator
from ttkbootstrap.widgets import ToolTip
from src.gui.loading_popup import LoadingPopup
from src.gui.results_popup import ResultsPopup
from src.model.enum.banner_type import BannerType
from src.gui.banner_selector import BannerSelector
from src.model.enum.simulation_type import SimulationType
from src.util.paths import get_external_path, get_resource_path
from src.gui.helpers.screen import calculate_screen_center_x, calculate_screen_center_y, get_screen_height, get_screen_width


class MainWindow(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")

        self.icon = None

        self.current_jewels = ttk.StringVar(value="0")
        self.platinum_tickets = ttk.StringVar(value="0")
        self.platinum_millicoins = ttk.StringVar(value="0")
        self.buy_bp = ttk.IntVar(value=0)
        self.buy_sub = ttk.IntVar(value=0)
        self.bp_days_left = ttk.StringVar(value="0")
        self.sub_days_left = ttk.StringVar(value="0")
        self.starting_pity_char = ttk.StringVar(value="0")
        self.starting_pity_weapon = ttk.StringVar(value="0")
        self.banner_type = ttk.IntVar(value=BannerType.TARGETED.value)
        self.simulation_type = ttk.IntVar(value=SimulationType.AVERAGE_LUCK.value)
        self.patch_data = self._load_patch_data()

        self.banner_selector = None
        self.loading_popup = None

        self._add_scroll_config()
        self._build_gui()
        self._init_app_window()


    def _init_app_window(self):
        self.update_idletasks()

        required_width = self.main_container.winfo_reqwidth() + 40
        required_height = self.main_container.winfo_reqheight() + 20

        screen_width = get_screen_width(self)
        screen_height = get_screen_height(self)

        app_width = min(required_width, int(screen_width * 0.9))
        app_height = min(int(required_height), int(screen_height * 0.9))

        app_pos_x = calculate_screen_center_x(self, app_width)
        app_pos_y = calculate_screen_center_y(self, app_height)

        self.title("P5X Gacha Pull Calculator")
        self.geometry(f"{app_width}x{app_height}+{app_pos_x}+{app_pos_y}")
        self._set_icon()

        pywinstyles.apply_style(self, "dark")


    def _set_icon(self):
        icon_path = get_resource_path("assets/app_icon.png")

        self.icon = PhotoImage(file=str(icon_path))
        self.iconphoto(True, self.icon)

        ico_path = get_resource_path("assets/app_icon.ico")
        if ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
            except:
                pass


    def _build_gui(self):
        vcmd = (self.register(validators.validate_integer), "%P")

        inputs_container = ttk.Frame(self.main_container)
        inputs_container.pack(expand=True, fill="x", anchor="n")

        self._build_user_inputs(inputs_container, vcmd)
        self._build_banner_selector(inputs_container)

        button_frame = ttk.Frame(inputs_container)
        button_frame.pack(fill="x", pady=10)

        start_calc_btn = ttk.Button(
            button_frame,
            text="Run Simulation",
            style="info.TButton",
            command=self._run_simulation
        )
        start_calc_btn.pack(anchor="center")


    def _build_user_inputs(self, container, vcmd):
        resource_frame = ttk.Frame(container)
        resource_frame.pack(fill="x", pady=(0, 10))

        resource_frame.columnconfigure(0, weight=0)
        resource_frame.columnconfigure(1, weight=0)
        resource_frame.columnconfigure(2, weight=0, minsize=30)
        resource_frame.columnconfigure(3, weight=0)
        resource_frame.columnconfigure(4, weight=0, minsize=30)
        resource_frame.columnconfigure(5, weight=0)


        current_jewels_label = ttk.Label(resource_frame, text="Current Meta Jewels")
        current_jewels_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        current_jewels_input = ttk.Entry(
            resource_frame,
            justify="right",
            textvariable=self.current_jewels,
            validate="key",
            validatecommand=vcmd,
            width=12
        )
        current_jewels_input.grid(row=1, column=0, sticky="w", pady=(0, 10), padx=(0, 10))
        current_jewels_input.bind("<FocusOut>", self._handle_empty_input_field)
        ToolTip(
            current_jewels_input,
            bootstyle="inverse-dark",
            text=f"Your currently held meta jewels. \r\n"
                 f"If at the beginning of a patch add either 6.000 or 10.000 based on patch type. \r\n"
                 f"For reference, check the \"Patch Select\" table: \r\n"
                 f"Red: Big Patch, add 10.000 Jewels to your count. \r\n"
                 f"White: Small Patch, add 6.000 Jewels to your count."
        )


        platinum_tickets_label = ttk.Label(resource_frame, text="Platinum Tickets")
        platinum_tickets_label.grid(row=2, column=0, sticky="w", padx=(0, 10))

        platinum_tickets_input = ttk.Entry(
            resource_frame,
            justify="right",
            textvariable=self.platinum_tickets,
            validate="key",
            validatecommand=vcmd,
            width=12
        )
        platinum_tickets_input.grid(row=3, column=0, sticky="w", pady=(0, 10), padx=(0, 10))
        platinum_tickets_input.bind("<FocusOut>", self._handle_empty_input_field)


        platinum_millicoins_label = ttk.Label(resource_frame, text="Platinum Millicoins")
        platinum_millicoins_label.grid(row=4, column=0, sticky="w", padx=(0, 10))

        platinum_millicoins_input = ttk.Entry(
            resource_frame,
            justify="right",
            textvariable=self.platinum_millicoins,
            validate="key",
            validatecommand=vcmd,
            width=12
        )
        platinum_millicoins_input.grid(row=5, column=0, sticky="w", pady=(0, 10), padx=(0, 10))
        platinum_millicoins_input.bind("<FocusOut>", self._handle_empty_input_field)


        starting_pity_char_label = ttk.Label(resource_frame, text="Starting Pity (Character)")
        starting_pity_char_label.grid(row=0, column=2, sticky="w", padx=(0, 10))

        starting_pity_char_input = ttk.Entry(
            resource_frame,
            justify="right",
            textvariable=self.starting_pity_char,
            validate="key",
            validatecommand=vcmd,
            width=12
        )
        starting_pity_char_input.grid(row=1, column=2, sticky="w", pady=(0, 10), padx=(0, 10))
        starting_pity_char_input.bind("<FocusOut>", self._handle_empty_input_field)
        ToolTip(
            starting_pity_char_input,
            bootstyle="inverse-dark",
            text=f"Your current pity on the banner type you want to summon on. \r\n"
                 f"A maximum of 79 for the Chance (50/50) banner or a maximum of 109 for the targeted (110, Guaranteed) banner."
        )


        starting_pity_weapon_label = ttk.Label(resource_frame, text="Starting Pity (Weapon)")
        starting_pity_weapon_label.grid(row=2, column=2, sticky="w", padx=(0, 10))

        starting_pity_weapon_input = ttk.Entry(
            resource_frame,
            justify="right",
            textvariable=self.starting_pity_weapon,
            validate="key",
            validatecommand=vcmd,
            width=12
        )
        starting_pity_weapon_input.grid(row=3, column=2, sticky="w", pady=(0, 10), padx=(0, 10))
        starting_pity_weapon_input.bind("<FocusOut>", self._handle_empty_input_field)


        bp_frame = ttk.Frame(resource_frame)
        bp_frame.grid(row=0, column=3, rowspan=2, sticky="nw", padx=(20, 0))

        buy_bp_check = ttk.Checkbutton(
            bp_frame,
            variable=self.buy_bp,
            text="Buy Phantom Pass?",
            style="CheckButton",
            command=lambda: self._toggle_remaining_days_input(self.buy_bp, bp_days_input, self.bp_days_left)
        )
        buy_bp_check.pack(anchor="w", pady=(0, 5))
        buy_bp_check.state(["!alternate"])

        bp_input_container = ttk.Frame(bp_frame)
        bp_input_container.pack(anchor="w")

        bp_days_input = ttk.Entry(
            bp_input_container,
            justify="right",
            textvariable=self.bp_days_left,
            validate="key",
            validatecommand=vcmd,
            width=8,
            state="disabled"
        )
        bp_days_input.pack(side="left", padx=(0, 5))
        bp_days_input.bind("<FocusOut>", self._handle_empty_input_field)

        bp_days_label = ttk.Label(bp_input_container, text="Days Left")
        bp_days_label.pack(side="left")


        sub_frame = ttk.Frame(resource_frame)
        sub_frame.grid(row=2, column=3, rowspan=2, sticky="nw", padx=(20, 0))

        buy_sub_check = ttk.Checkbutton(
            sub_frame,
            variable=self.buy_sub,
            text="Buy Monthly Sub?",
            style="CheckButton",
            command=lambda: self._toggle_remaining_days_input(self.buy_sub, sub_days_input, self.sub_days_left)
        )
        buy_sub_check.pack(anchor="w", pady=(0, 5))
        buy_sub_check.state(["!alternate"])

        sub_input_container = ttk.Frame(sub_frame)
        sub_input_container.pack(anchor="w")

        sub_days_input = ttk.Entry(
            sub_input_container,
            justify="right",
            textvariable=self.sub_days_left,
            validate="key",
            validatecommand=vcmd,
            width=8,
            state="disabled"
        )
        sub_days_input.pack(side="left", padx=(0, 5))
        sub_days_input.bind("<FocusOut>", self._handle_empty_input_field)

        sub_days_label = ttk.Label(sub_input_container, text="Days Left")
        sub_days_label.pack(side="left")


        radio_container = ttk.Frame(resource_frame)
        radio_container.grid(row=0, column=4, rowspan=6, sticky="n", padx=(30, 0))


        banner_group = ttk.Frame(radio_container)
        banner_group.pack(anchor="w", pady=(0, 15))

        banner_type_select_label = ttk.Label(banner_group, text="Banner Type:")
        banner_type_select_label.pack(anchor="w", pady=(0, 5))

        char_targeted_radio = ttk.Radiobutton(
            banner_group,
            text="Targeted (110 Pity, Guaranteed)",
            variable=self.banner_type,
            value=BannerType.TARGETED.value
        )
        char_targeted_radio.pack(anchor="w", pady=(0, 2))

        char_chance_radio = ttk.Radiobutton(
            banner_group,
            text="Chance (80 Pity, 50/50)",
            variable=self.banner_type,
            value=BannerType.CHANCE.value
        )
        char_chance_radio.pack(anchor="w")


        sim_group = ttk.Frame(radio_container)
        sim_group.pack(anchor="w")

        simulation_type_label = ttk.Label(sim_group, text="Simulate for:")
        simulation_type_label.pack(anchor="w", pady=(0, 5))

        sim_type_average_radio = ttk.Radiobutton(
            sim_group,
            text="Average Luck",
            variable=self.simulation_type,
            value=SimulationType.AVERAGE_LUCK.value
        )
        sim_type_average_radio.pack(anchor="w", pady=(0, 2))
        ToolTip(
            sim_type_average_radio,
            bootstyle="inverse-dark",
            text=f"Run the simulation under mathematically average luck."
        )

        sim_type_below_average_radio = ttk.Radiobutton(
            sim_group,
            text="Below Average Luck",
            variable=self.simulation_type,
            value=SimulationType.BELOW_AVERAGE_LUCK.value
        )
        sim_type_below_average_radio.pack(anchor="w", pady=(0, 2))
        ToolTip(
            sim_type_below_average_radio,
            bootstyle="inverse-dark",
            text=f"Run the simulator assuming below average luck in your pulls."
        )

        sim_type_worst_radio = ttk.Radiobutton(
            sim_group,
            text="Worst Possible Luck",
            variable=self.simulation_type,
            value=SimulationType.WORST_LUCK.value
        )
        sim_type_worst_radio.pack(anchor="w")
        ToolTip(
            sim_type_worst_radio,
            bootstyle="inverse-dark",
            text=f"This will run simulation with the worst possible luck. \r\n"
                 f"It will assume you always hit hard pity and lose every 50/50 possible."
        )


    def _build_banner_selector(self, container):
        banner_select_label = ttk.Label(container, text="Patch Select")
        banner_select_label.pack(anchor="w", pady=(10,5))

        self.banner_selector = BannerSelector(
            container,
            self.patch_data
        )
        self.banner_selector.pack(fill="x", pady=(0, 5))

        def _handle_banner_scroll(e):
            return "break" if hasattr(self.banner_selector, 'internal_canvas') else None

        self.banner_selector.bind("<MouseWheel>", _handle_banner_scroll)


    def _run_simulation(self):
        sim = Simulator(
            self.simulation_type.get(),
            self.banner_type.get(),
            self.current_jewels.get(),
            self.platinum_tickets.get(),
            self.platinum_millicoins.get(),
            self.starting_pity_char.get(),
            self.starting_pity_weapon.get(),
            self.buy_bp.get(),
            self.bp_days_left.get(),
            self.buy_sub.get(),
            self.sub_days_left.get(),
            self.banner_selector.get_selections()
        )

        self.loading_popup = LoadingPopup(self)
        self.loading_popup.lift()
        self.loading_popup.grab_set()

        thread = threading.Thread(target=self._run_simulation_thread, args=(sim,), daemon=True)
        thread.start()


    def _run_simulation_thread(self, sim):
        try:
            results = sim.run_simulations()

            self.after(0, self._on_simulation_complete, results)
        except Exception as e:
            self.after(0, self._on_simulation_error, str(e))


    def _on_simulation_complete(self, results):
        if self.loading_popup:
            self.loading_popup.close()
            self.loading_popup = None

        results_popup = ResultsPopup(self, results)
        results_popup.lift()
        results_popup.grab_set()


    def _on_simulation_error(self, error_message):
        if self.loading_popup:
            self.loading_popup.close()
            self.loading_popup = None

        messagebox.showerror("Simulation Error", f"Error running simulation: {error_message}")


    def _add_scroll_config(self):
        canvas = ttk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview, bootstyle="round")

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        scrollable_frame = ttk.Frame(canvas)
        self.main_container = ttk.Frame(scrollable_frame)
        self.main_container.pack(anchor="nw", padx=20, pady=10)

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            if canvas.winfo_width() > 1:
                canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        scrollable_frame.bind("<Configure>", on_frame_configure)

        def _on_mousescroll(e):
            widget = self.winfo_containing(e.x_root, e.y_root)

            if widget and self.banner_selector:
                current = widget
                while current:
                    if current == self.banner_selector:
                        return "break"
                    current = current.master

            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            return "break"

        canvas.bind_all("<MouseWheel>", _on_mousescroll)

        canvas.configure(scrollregion=canvas.bbox("all"))



    @staticmethod
    def _handle_empty_input_field(event):
        widget = event.widget

        if widget.get() == "":
            widget.delete(0, "end")
            widget.insert(0, "0")


    @staticmethod
    def _toggle_remaining_days_input(checkbox_var, input_widget, days_var):
        if checkbox_var.get():
            input_widget.config(state="normal")
        else:
            input_widget.config(state="disabled")
            days_var.set("0")


    @staticmethod
    def _load_patch_data():
        try:
            json_path = get_external_path("patch_db.json")

            with open(json_path, "r") as f:
                return json.load(f)

        except FileNotFoundError:
            print(f"Warning: patch_db.json not found at {json_path}")
            return {}