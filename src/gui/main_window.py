import json
import threading
import pywinstyles
import ttkbootstrap as ttk
import src.gui.helpers.validators as validators
from pathlib import Path
from tkinter import PhotoImage
from src.core.simulator import Simulator
from ttkbootstrap.widgets import ToolTip
from src.gui.loading_popup import LoadingPopup
from src.model.enum.banner_type import BannerType
from src.gui.banner_selector import BannerSelector
from src.model.enum.simulation_type import SimulationType
from src.util.paths import get_external_path, get_resource_path
from src.gui.helpers.build_character_name_string import build_character_name_string
from src.gui.helpers.screen import calculate_screen_center_x, calculate_screen_center_y

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
        self.result_frame = None
        self.loading_popup = None

        self._init_app_window()
        self._build_gui()


    def _init_app_window(self):
        app_width = 800
        app_height = 800

        self.update_idletasks()
        app_pos_x = calculate_screen_center_x(self, app_width)
        app_pos_y = calculate_screen_center_y(self, app_height)

        self.title("P5X Gacha Pull Calculator")
        self.geometry(f"{app_width}x{app_height}+{app_pos_x}+{app_pos_y}")
        self.resizable(False, False)
        self._set_icon()

        pywinstyles.apply_style(self, "dark")


    def _set_icon(self):
        src_dir = Path(__file__).parent.parent
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

        container = ttk.Frame(self)
        container.pack(expand=True, fill="both", padx=20, pady=10)

        inputs_container = ttk.Frame(container)
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

        self.result_frame = ttk.Frame(inputs_container) #This is false? It should probably be in its own container, I assume?
        self.result_frame.pack(fill="x", pady=(20,0))


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
            self.patch_data,
            height=200
        )
        self.banner_selector.pack(fill="x", pady=(0, 5))


    def _run_simulation(self):
        for widget in self.result_frame.winfo_children():
            widget.destroy()

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

        self._display_results(results)


    def _on_simulation_error(self, error_message):
        if self.loading_popup:
            self.loading_popup.close()
            self.loading_popup = None

        error_label = ttk.Label(
            self.result_frame,
            text=f"Error running simulation: {error_message}",
            bootstyle="danger",
            font=("TkDefaultFont", 10)
        )
        error_label.pack(anchor="center", pady=20)


    def _display_results(self, results):
        success_rate = results["success_rate"]
        successful_runs = results["successful_runs"]
        total_runs = results["total_runs"]

        separator = ttk.Separator(self.result_frame, orient="horizontal")
        separator.pack(fill="x", pady=(0, 15))


        title_label = ttk.Label(
            self.result_frame,
            text="Simulation Results",
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.pack(anchor="center", pady=(0, 10))


        stats_container = ttk.Frame(self.result_frame)
        stats_container.pack(fill="both", expand=True, pady=(10, 0))

        stats_container.columnconfigure(0, weight=1)
        stats_container.columnconfigure(1, weight=1)

        # Overall Statistics
        left_frame = ttk.Frame(stats_container)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))


        left_title = ttk.Label(
            left_frame,
            text="Overall Success Rate",
            font=("TkDefaultFont", 11, "bold")
        )
        left_title.pack(anchor="w", pady=(0, 10))


        if success_rate >= 75:
            color_style = "success"
        elif success_rate >= 50:
            color_style = "warning"
        else:
            color_style = "danger"

        success_label = ttk.Label(
            left_frame,
            text=f"{success_rate:.2f}%",
            font=("TkDefaultFont", 20, "bold"),
            bootstyle=color_style
        )
        success_label.pack(anchor="w", pady=(0, 5))


        details_label = ttk.Label(
            left_frame,
            text=f"Successfully obtained all desired characters and weapons\nin {successful_runs:,} out of {total_runs:,} simulations",
            font=("TkDefaultFont", 9),
            justify="left"
        )
        details_label.pack(anchor="w", pady=(0, 10))


        # Failure point analysis
        if results.get("failure_breakdown"):
            right_frame = ttk.Frame(stats_container)
            right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

            failure_title = ttk.Label(
                right_frame,
                text="Failure Points",
                font=("TkDefaultFont", 11, "bold")
            )
            failure_title.pack(anchor="w", pady=(0, 10))


            canvas = ttk.Canvas(right_frame, highlightthickness=0)
            scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
            failure_list_frame = ttk.Frame(canvas)

            failure_list_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=failure_list_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)


            canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
            failure_list_frame.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")


            for (banner_version, failure_type, name), data in results["failure_breakdown"]:
                count = data["count"]
                failure_pct = (count / total_runs) * 100
                char_name = build_character_name_string(name)

                if failure_type == "character":
                    failure_text = f"Patch {banner_version}: Failed to obtain {char_name}"
                elif failure_type == "weapon":
                    failure_text = f"Patch {banner_version}: Failed to obtain {char_name}'s weapon."
                elif failure_type == "duplicate":
                    if data["obtained_list"]:
                        avg_obtained = sum(data["obtained_list"]) / len(data["obtained_list"])
                        failure_text = f"Patch {banner_version}: Failed to obtain all of {char_name}'s\nAwarenesses (Avg: {avg_obtained:.1f} of {data["needed"]})"
                    else:
                        failure_text = f"Patch {banner_version}: Failed to obtain all of {char_name}'s\nAwarenesses"
                elif failure_type == "refinement":
                    if data["obtained_list"]:
                        avg_obtained = sum(data["obtained_list"]) / len(data["obtained_list"])
                        failure_text = f"Patch {banner_version}: Failed to obtain all {char_name}\nRefinements (Avg: {avg_obtained:.1f} of {data["needed"]})"
                    else:
                        failure_text = f"Patch {banner_version}: Failed to obtain all {char_name}\nRefinements"
                else:
                    failure_text = f"Patch {banner_version}: {failure_type}"

                failure_label = ttk.Label(
                    failure_list_frame,
                    text=failure_text,
                    font=("TkDefaultFont", 9, "bold"),
                    justify="left"
                )
                failure_label.pack(anchor="w", pady=(0, 2))
                failure_label.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

                failure_pct_label = ttk.Label(
                    failure_list_frame,
                    text=f"Failed in {failure_pct:.1f}% of runs ({count:,} / {total_runs:,})",
                    font=("TkDefaultFont", 8),
                    foreground="gray",
                    justify="left"
                )
                failure_pct_label.pack(anchor="w", pady=(0, 12))
                failure_pct_label.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))


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