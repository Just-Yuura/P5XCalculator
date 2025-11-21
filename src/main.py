import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

import multiprocessing
from src.gui.main_window import MainWindow
from src.data.patch_db_updater import DBUpdater


if __name__ == "__main__":
    multiprocessing.freeze_support()

    db_updater = DBUpdater()
    db_updater.check_and_update()

    window = MainWindow()
    window.mainloop()
