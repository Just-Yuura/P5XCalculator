import ttkbootstrap as ttk
from src.gui.helpers.screen import calculate_screen_center_x, calculate_screen_center_y, get_screen_height, \
    get_screen_width
from src.gui.helpers.build_character_name_string import build_character_name_string


class ResultsPopup(ttk.Toplevel):
    def __init__(self, parent, results):
        super().__init__(parent)
        self.title("Simulation Results")
        self.geometry("600x500")
        self.resizable(True, True)

        self.update_idletasks()
        pos_x = calculate_screen_center_x(self, 600)
        pos_y = calculate_screen_center_y(self, 500)
        self.geometry(f"+{pos_x}+{pos_y}")

        self.transient(parent)
        self.grab_set()

        self._build_results(results)

    def _build_results(self, results):
        success_rate = results["success_rate"]
        successful_runs = results["successful_runs"]
        total_runs = results["total_runs"]

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        text_widget = ttk.Text(container, wrap="word", state="normal")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True)

        text_widget.tag_configure("title", font=("TkDefaultFont", 14, "bold"), spacing3=20)
        text_widget.tag_configure("success", font=("TkDefaultFont", 16, "bold"), foreground="green")
        text_widget.tag_configure("warning", font=("TkDefaultFont", 16, "bold"), foreground="orange")
        text_widget.tag_configure("danger", font=("TkDefaultFont", 16, "bold"), foreground="red")
        text_widget.tag_configure("details", font=("TkDefaultFont", 9), spacing3=20)
        text_widget.tag_configure("section_title", font=("TkDefaultFont", 12, "bold"), spacing1=10, spacing3=10)
        text_widget.tag_configure("failure_text", font=("TkDefaultFont", 9, "bold"), spacing3=2)
        text_widget.tag_configure("failure_pct", font=("TkDefaultFont", 8), foreground="gray", spacing3=12)

        text_widget.insert("end", "Simulation Results\n", "title")

        if success_rate >= 75:
            color_style = "success"
        elif success_rate >= 50:
            color_style = "warning"
        else:
            color_style = "danger"

        text_widget.insert("end", f"Success Rate: {success_rate:.2f}%\n", color_style)
        text_widget.insert(
            "end",
            f"Successfully obtained all desired characters and weapons\nin {successful_runs:,} out of {total_runs:,} simulations\n",
            "details"
        )

        if results.get("failure_breakdown"):
            text_widget.insert("end", "Failure Points\n", "section_title")

            for (banner_version, failure_type, name), data in results["failure_breakdown"]:
                count = data["count"]
                failure_pct = (count / total_runs) * 100
                char_name = build_character_name_string(name)

                if failure_type == "character":
                    failure_text = f"Patch {banner_version}: Failed to obtain {char_name}\n"
                elif failure_type == "weapon":
                    failure_text = f"Patch {banner_version}: Failed to obtain {char_name}'s weapon\n"
                elif failure_type == "duplicate":
                    if data["obtained_list"]:
                        avg_obtained = sum(data["obtained_list"]) / len(data["obtained_list"])
                        failure_text = f"Patch {banner_version}: Failed to obtain all of {char_name}'s Awarenesses (Avg: {avg_obtained:.1f} of {data['needed']})\n"
                    else:
                        failure_text = f"Patch {banner_version}: Failed to obtain all of {char_name}'s Awarenesses\n"
                elif failure_type == "refinement":
                    if data["obtained_list"]:
                        avg_obtained = sum(data["obtained_list"]) / len(data["obtained_list"])
                        failure_text = f"Patch {banner_version}: Failed to obtain all {char_name} Refinements (Avg: {avg_obtained:.1f} of {data['needed']})\n"
                    else:
                        failure_text = f"Patch {banner_version}: Failed to obtain all {char_name} Refinements\n"
                else:
                    failure_text = f"Patch {banner_version}: {failure_type}\n"

                text_widget.insert("end", failure_text, "failure_text")
                text_widget.insert(
                    "end",
                    f"Failed in {failure_pct:.1f}% of runs ({count:,} / {total_runs:,})\n",
                    "failure_pct"
                )

        text_widget.configure(state="disabled")
        text_widget.configure(padx=10, pady=10)