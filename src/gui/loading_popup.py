import pywinstyles
import ttkbootstrap as ttk


class LoadingPopup(ttk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Running Simulation")
        self.geometry("400x150")
        self.resizable(False, False)

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (150 // 2)
        self.geometry(f"+{x}+{y}")

        self.transient(parent)
        self.grab_set()

        container = ttk.Frame(self, padding=20)
        container.pack(expand=True, fill="both")

        label = ttk.Label(
            container,
            text="Running simulations...",
            font=("TkDefaultFont", 11)
        )
        label.pack(pady=(10, 20))

        self.progress = ttk.Progressbar(
            container,
            mode="indeterminate",
            bootstyle="info",
            length=300
        )
        self.progress.pack(pady=(0, 10))
        self.progress.start(10)

        self.status_label = ttk.Label(
            container,
            text="Please wait...",
            font=("TkDefaultFont", 9),
            foreground="gray"
        )
        self.status_label.pack()

        pywinstyles.apply_style(self, "dark")


    def close(self):
        self.progress.stop()
        self.grab_release()
        self.destroy()