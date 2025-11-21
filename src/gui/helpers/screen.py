def calculate_screen_center_x(window, width):
    screen_width = get_screen_width(window)
    return (screen_width - width) // 2


def calculate_screen_center_y(window, height):
    screen_height = get_screen_height(window)
    return (screen_height - height) // 2


def get_screen_width(window):
    return window.winfo_screenwidth()


def get_screen_height(window):
    return window.winfo_screenheight()