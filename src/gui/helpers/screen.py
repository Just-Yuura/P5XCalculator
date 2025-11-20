def calculate_screen_center_x(window, width):
    screen_width = window.winfo_screenwidth()
    return (screen_width - width) // 2


def calculate_screen_center_y(window, height):
    screen_height = window.winfo_screenheight()
    return (screen_height - height) // 2