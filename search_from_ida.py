import os
import webbrowser
try:
    from urllib.parse import urlparse  # Python 3
except ImportError:
    from urlparse import urlparse  # Python 2

import ida_idaapi
import ida_kernwin

QUERY_URL_FORMAT = 'https://google.com/search?q="{}"'

PLUGIN_NAME = ACTION_NAME = 'Search from IDA'
ACTION_LABEL_FORMAT = 'Search for "{}"'
ICONS_DIRECTORY_NAME = 'icons'
ICON_FILE_EXTENSION = '.png'
SUPPORTED_BUILTIN_WINDOWS = (ida_kernwin.BWN_DISASM, ida_kernwin.BWN_PSEUDOCODE)


def _get_highlight(widget):
    highlight = ida_kernwin.get_highlight(widget)
    if highlight:
        return highlight[0]
    else:
        return ''


def _should_enable_action(widget):
    if ida_kernwin.get_widget_type(widget) not in SUPPORTED_BUILTIN_WINDOWS:
        return False
    if not _get_highlight(widget):
        return False
    return True


class SearchHandler(ida_kernwin.action_handler_t):
    def activate(self, ctx):
        webbrowser.open_new_tab(QUERY_URL_FORMAT.format(_get_highlight(ctx.widget)))

    def update(self, ctx):
        if _should_enable_action(ctx.widget):
            return ida_kernwin.AST_ENABLE
        else:
            return ida_kernwin.AST_DISABLE


class ContextMenuHooks(ida_kernwin.UI_Hooks):
    def finish_populating_widget_popup(self, widget, popup_handle):
        if _should_enable_action(widget):
            highlight = _get_highlight(widget)
            ida_kernwin.update_action_label(ACTION_NAME, ACTION_LABEL_FORMAT.format(highlight))
            ida_kernwin.attach_action_to_popup(widget, popup_handle, ACTION_NAME, None)


class SearchFromIda(ida_idaapi.plugin_t):
    flags = ida_idaapi.PLUGIN_HIDE
    comment = PLUGIN_NAME
    help = ''
    wanted_name = PLUGIN_NAME
    wanted_hotkey = ''

    _hooks = ContextMenuHooks()

    @staticmethod
    def _get_icon_path():
        fqdn = urlparse(QUERY_URL_FORMAT).netloc
        icon_filename = os.path.join(ICONS_DIRECTORY_NAME, fqdn + ICON_FILE_EXTENSION)
        icon_path = os.path.join(os.path.dirname(__file__), icon_filename)
        return icon_path

    def _update_action_icon(self):
        """
        If you think this function is awkward, you are not mistaken.
        This helps circumventing certain bugs in the icons API.
        """
        icon_path = self._get_icon_path()
        if not os.path.exists(icon_path):
            print('[{}] File {} does not exist.'.format(PLUGIN_NAME, icon_path))
            self._action_icon = 0
        else:
            self._action_icon = ida_kernwin.load_custom_icon(icon_path)
            if self._action_icon:
                ida_kernwin.update_action_icon(ACTION_NAME, self._action_icon)

    def init(self):
        action_desc = ida_kernwin.action_desc_t(ACTION_NAME,
                                                ACTION_NAME,
                                                SearchHandler())

        ida_kernwin.register_action(action_desc)
        self._update_action_icon()

        self._hooks.hook()

        return ida_idaapi.PLUGIN_KEEP

    def run(self):
        pass

    def term(self):
        self._hooks.unhook()
        if self._action_icon:
            ida_kernwin.free_custom_icon(self._action_icon)


def PLUGIN_ENTRY():
    return SearchFromIda()
