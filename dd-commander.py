import os

from prompt_toolkit import Application
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame

app: Application
cursor_position = 0
status_window = None


class PaneItem:
    def __init__(self, path, filename=None, is_dir=False, is_go_up=False):
        self.path = path
        self.filename = filename
        self.is_dir = is_dir
        self.is_go_up = is_go_up
        self.selected = False
        self.caption = None
        self.set_caption()

    def select(self):
        self.selected = True
        self.set_caption()

    def deselect(self):
        self.selected = False
        self.set_caption()

    def set_caption(self):
        self.caption = ".." if self.is_go_up else self.filename


class Pane:
    def __init__(self, path):
        self.content = ".."
        self.cursor_position = 0
        self.items = []
        self.path = path
        self.window = None
        self.set_path(path)

    def select_item(self, index):
        for i, item in enumerate(self.items):
            if i == index:
                item.select()
            else:
                item.deselect()
        self.cursor_position = index

    def focus(self):
        self.window.style = self.get_window_style(True)

    def unfocus(self):
        self.window.style = self.get_window_style(False)

    def set_path(self, path):
        self.path = path
        files = os.listdir(path)

        self.items = [PaneItem(path, filename="go_up", is_go_up=True)]
        for str_item in files:
            full_path = os.path.join(path, str_item)
            if os.path.isdir(full_path):
                self.items.append(PaneItem(full_path, filename=str_item, is_dir=True))
            else:
                self.items.append(PaneItem(full_path, filename=str_item, is_dir=False))

        self.select_item(0)

    def get_window_style(self, is_focused=False):
        return f'class:pane{".selected" if is_focused else ""}'

    def create_window(self):
        return Window(self.render_selection())

    def get_window(self, is_focused=False):
        if self.window is None:
            self.window = self.create_window()
        else:
            self.window.content = self.render_selection()
        self.window.style = self.get_window_style(is_focused)
        return self.window

    def move_selection(self, app, direction):
        new_position = (self.cursor_position + direction) % len(self.items)
        self.select_item(new_position)
        self.window.content = self.render_selection()
        if app:
            app.invalidate()

    def render_selection(self):
        result = []
        for item in self.items:
            style = 'class:selected' if item.selected else ''
            result.append((style, f"{item.caption}\n"))
        return FormattedTextControl(result)


focused_pane: Pane
left_pane: Pane
right_pane: Pane


def get_style():
    return Style.from_dict({
        'frame.border': '#888888',
        'selected': 'reverse',
        'pane.selected': 'fg:#ffffff bg:#444444',
        'pane': 'fg:#888888 bg:#111111',
        "status_bar": "bg:#888888 fg:#ffffff",
    })


def get_layout_components():
    l_pane = Pane(os.getcwd())
    r_pane = Pane(os.getcwd())
    left_pane_window = l_pane.get_window()
    right_pane_window = r_pane.get_window()
    s_window = Window(height=1, content=FormattedTextControl(HTML(get_keybinds_status_string())),
                      style='class:status_bar', align=WindowAlign.LEFT)

    root = Layout(Frame(HSplit(
        [VSplit([Frame(left_pane_window, title=l_pane.path), Frame(right_pane_window, title=r_pane.path), ]),
         Frame(s_window, title="STATUS")]), title="DD_COMMANDER"))

    return root, l_pane, r_pane, s_window


def get_keybinds_status_string():
    return ("F1:Help F2:Menu F3:View F4:Edit F5:Copy F6:Move/Rename F7:MkDir F8:Delete "
            "F10:Quit Tab:Switch Enter:Open/Exec Ctrl+U:Swap Ctrl+R:Refresh "
            "Ctrl+O:CmdLine ")


def get_keys():
    kb = KeyBindings()

    @kb.add('up')
    def _(event):
        """scroll up"""
        focused_pane.move_selection(app=event.app, direction=-1)

    @kb.add('down')
    def _(event):
        """scroll down"""
        focused_pane.move_selection(app=event.app, direction=1)

    @kb.add('tab')
    def _(event):
        """Switch between panels"""
        global focused_pane
        focused_pane.unfocus()
        if focused_pane is left_pane:
            focused_pane = right_pane
        else:
            focused_pane = left_pane
        focused_pane.focus()
        event.app.invalidate()

    @kb.add('f10')
    def _(event):
        """Quit"""
        event.app.exit()

    # Add other key bindings here...

    return kb


def startup():
    global app, focused_pane, left_pane, right_pane, status_window, cursor_position
    root, l_pane, r_pane, s_window = get_layout_components()

    left_pane = l_pane
    right_pane = r_pane
    status_window = s_window
    focused_pane = left_pane
    focused_pane.focus()

    app = Application(
        layout=root,
        key_bindings=get_keys(),
        full_screen=True,
        style=get_style(),
        mouse_support=True,
        cursor=None
    )
    app.run()


# Run the application
if __name__ == '__main__':
    startup()
