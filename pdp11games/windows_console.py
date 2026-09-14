"""The small curses interface the console games need, implemented with Win32 console APIs.

SPDX-License-Identifier: GPL-3.0-or-later
Uses only the Python standard library. Imported instead of curses on Windows.
"""
import ctypes as ct
import time

KEY_DOWN, KEY_UP, KEY_LEFT, KEY_RIGHT = 258, 259, 260, 261
KEY_BACKSPACE = 263
_current_screen = None
KEY_EVENT = 1
ENABLE_EXTENDED_FLAGS = 0x0080
ENABLE_WINDOW_INPUT = 0x0008
# Fixed-width Win32 types keep the ABI testable even on non-Windows hosts.
WORD, DWORD, BOOL, SHORT, HANDLE = ct.c_uint16, ct.c_uint32, ct.c_int32, ct.c_int16, ct.c_void_p


class COORD(ct.Structure):
    _fields_ = [('X', SHORT), ('Y', SHORT)]


class SMALL_RECT(ct.Structure):
    _fields_ = [('Left', SHORT), ('Top', SHORT), ('Right', SHORT), ('Bottom', SHORT)]


class CHAR_UNION(ct.Union):
    _fields_ = [('UnicodeChar', WORD), ('AsciiChar', ct.c_char)]


class CHAR_INFO(ct.Structure):
    _fields_ = [('Char', CHAR_UNION), ('Attributes', WORD)]


class KEY_EVENT_RECORD(ct.Structure):
    _fields_ = [('bKeyDown', BOOL), ('wRepeatCount', WORD), ('wVirtualKeyCode', WORD),
                ('wVirtualScanCode', WORD), ('uChar', CHAR_UNION), ('dwControlKeyState', DWORD)]


class EVENT_UNION(ct.Union):
    _fields_ = [('KeyEvent', KEY_EVENT_RECORD), ('padding', ct.c_byte * 16)]


class INPUT_RECORD(ct.Structure):
    _fields_ = [('EventType', WORD), ('Event', EVENT_UNION)]


class CONSOLE_SCREEN_BUFFER_INFO(ct.Structure):
    _fields_ = [('dwSize', COORD), ('dwCursorPosition', COORD), ('wAttributes', WORD),
                ('srWindow', SMALL_RECT), ('dwMaximumWindowSize', COORD)]


class CONSOLE_CURSOR_INFO(ct.Structure):
    _fields_ = [('dwSize', DWORD), ('bVisible', BOOL)]


class error(Exception):
    """Console unavailable, too small, or a native operation failed."""


def _api():
    dll = ct.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'GetStdHandle': ([DWORD], HANDLE),
        'GetConsoleMode': ([HANDLE, ct.POINTER(DWORD)], BOOL),
        'SetConsoleMode': ([HANDLE, DWORD], BOOL),
        'GetConsoleScreenBufferInfo': ([HANDLE, ct.POINTER(CONSOLE_SCREEN_BUFFER_INFO)], BOOL),
        'CreateConsoleScreenBuffer': ([DWORD, DWORD, ct.c_void_p, DWORD, ct.c_void_p], HANDLE),
        'SetConsoleActiveScreenBuffer': ([HANDLE], BOOL),
        'SetConsoleCursorPosition': ([HANDLE, COORD], BOOL),
        'SetConsoleCursorInfo': ([HANDLE, ct.POINTER(CONSOLE_CURSOR_INFO)], BOOL),
        'WriteConsoleOutputW': ([HANDLE, ct.POINTER(CHAR_INFO), COORD, COORD, ct.POINTER(SMALL_RECT)], BOOL),
        'GetNumberOfConsoleInputEvents': ([HANDLE, ct.POINTER(DWORD)], BOOL),
        'ReadConsoleInputW': ([HANDLE, ct.POINTER(INPUT_RECORD), DWORD, ct.POINTER(DWORD)], BOOL),
        'CloseHandle': ([HANDLE], BOOL),
    }
    for name, (args, result) in signatures.items():
        function = getattr(dll, name)
        function.argtypes = args
        function.restype = result
    return dll


def _check(result, operation):
    if not result:
        code = getattr(ct, 'get_last_error', lambda: 0)()
        raise error(f'{operation} failed (Windows error {code}). Run Xonix in a console window.')
    return result


def _key(record):
    if record.EventType != KEY_EVENT or not record.Event.KeyEvent.bKeyDown:
        return None
    event = record.Event.KeyEvent
    char = event.uChar.UnicodeChar
    if char == 3 or (event.wVirtualKeyCode == ord('C') and event.dwControlKeyState & 0x000C):
        raise KeyboardInterrupt
    arrows = {0x25: KEY_LEFT, 0x26: KEY_UP, 0x27: KEY_RIGHT, 0x28: KEY_DOWN}
    if event.wVirtualKeyCode in arrows:
        return arrows[event.wVirtualKeyCode]
    if char in (8, 127):
        return KEY_BACKSPACE
    if char == 13:
        return 10  # Match curses' Enter key.
    if char:
        return char
    return None


class Screen:
    width, height = 80, 24

    def __init__(self, api=None):
        self.api = api if api is not None else _api()
        self.output = None
        self.active = False
        self.mode_saved = False
        self.blocking = True
        self.echoing = False
        self.last_text = None
        self.cursor_y = self.cursor_x = 0
        self.repeats = 0
        self.repeat_key = -1
        self.input = self.api.GetStdHandle(DWORD(-10).value)
        self.original = self.api.GetStdHandle(DWORD(-11).value)
        self.original_mode = DWORD()
        try:
            _check(self.api.GetConsoleMode(self.input, ct.byref(self.original_mode)), 'GetConsoleMode')
            self.mode_saved = True
            info = self._info(self.original)
            self._require_size(info)
            self.attributes = info.wAttributes
            # A separate screen buffer preserves the shell contents and cursor.
            self.output = self.api.CreateConsoleScreenBuffer(0xC0000000, 3, None, 1, None)
            if self.output in (None, 0, ct.c_void_p(-1).value):
                self.output = None
                raise error('Cannot create a Windows console screen buffer.')
            self._require_size(self._info(self.output))
            cursor = CONSOLE_CURSOR_INFO(25, False)
            _check(self.api.SetConsoleCursorInfo(self.output, ct.byref(cursor)), 'SetConsoleCursorInfo')
            # Disable line input, echo, quick-edit and processed Ctrl-C. Ctrl-C
            # is read as a key so the normal Python cleanup path always runs.
            _check(self.api.SetConsoleMode(self.input, ENABLE_EXTENDED_FLAGS | ENABLE_WINDOW_INPUT), 'SetConsoleMode')
            _check(self.api.SetConsoleActiveScreenBuffer(self.output), 'SetConsoleActiveScreenBuffer')
            self.active = True
            self.cells = (CHAR_INFO * (self.width * self.height))()
            self.erase()
        except BaseException:
            self.close(ignore_errors=True)
            raise

    def _info(self, handle):
        info = CONSOLE_SCREEN_BUFFER_INFO()
        _check(self.api.GetConsoleScreenBufferInfo(handle, ct.byref(info)), 'GetConsoleScreenBufferInfo')
        return info

    def _require_size(self, info):
        window = info.srWindow
        if window.Right-window.Left+1 < self.width or window.Bottom-window.Top+1 < self.height:
            raise error('Your console window is too small. At least 80x24 is required.')

    def getmaxyx(self):
        info = self._info(self.output)
        self._require_size(info)
        return info.srWindow.Bottom-info.srWindow.Top+1, info.srWindow.Right-info.srWindow.Left+1

    def erase(self):
        self.cursor_y = self.cursor_x = 0
        for cell in self.cells:
            cell.Char.UnicodeChar = ord(' ')
            cell.Attributes = self.attributes

    def _put(self, y, x, text):
        if not 0 <= y < self.height:
            return
        for offset, char in enumerate(str(text)):
            column = x+offset
            if 0 <= column < self.width:
                cell = self.cells[y*self.width+column]
                if char in ("▉", "█"):
                    # A solid background works even with fonts lacking block glyphs.
                    cell.Char.UnicodeChar = ord(' ')
                    cell.Attributes = (self.attributes & ~0xF0) | ((self.attributes & 0x0F) << 4)
                else:
                    cell.Char.UnicodeChar = ord(char) if ord(char) <= 0xFFFF else ord('?')
                    # Moving actors and erased trails must restore the normal background.
                    cell.Attributes = self.attributes

    def move(self, y, x):
        if not (0 <= y < self.height and 0 <= x < self.width):
            raise error('Cursor position is outside the console game area.')
        self.cursor_y, self.cursor_x = y, x

    def getyx(self):
        return self.cursor_y, self.cursor_x

    def addstr(self, *args):
        if len(args) == 3:
            y, x, text = args
            self.move(y, x)
        elif len(args) == 1:
            text = args[0]
        else:
            raise TypeError('addstr expects text or y, x, text')
        for char in str(text):
            if char == '\n':
                self._put(self.cursor_y, self.cursor_x, ' ' * (self.width-self.cursor_x))
                self.cursor_y = min(self.height-1, self.cursor_y+1)
                self.cursor_x = 0
            elif char == '\r':
                self.cursor_x = 0
            else:
                self._put(self.cursor_y, self.cursor_x, char)
                self.cursor_x += 1
                if self.cursor_x == self.width:
                    self.cursor_x = 0
                    self.cursor_y = min(self.height-1, self.cursor_y+1)

    def insstr(self, text):
        start = self.cursor_y*self.width+self.cursor_x
        count = min(len(text),self.width-self.cursor_x)
        for i in range(self.width-self.cursor_x-count-1,-1,-1):
            self.cells[start+i+count] = self.cells[start+i]
        self._put(self.cursor_y,self.cursor_x,text[:count])

    def deleteln(self):
        start = self.cursor_y*self.width
        for i in range(start,(self.height-1)*self.width):
            self.cells[i] = self.cells[i+self.width]
        self._put(self.height-1,0,' '*self.width)

    def get_wch(self):
        value = self.getch()
        if self.last_text is not None:
            return self.last_text
        return value

    def getstr(self):
        y,x = self.getyx()
        text = ''
        echoing,self.echoing = self.echoing,False
        try:
            while True:
                key = self.get_wch()
                if key == '\n':
                    return text.encode('utf-8')
                if key == KEY_BACKSPACE:
                    text = text[:-1]
                elif isinstance(key,str) and key.isprintable() and len(text)<self.width-x-1:
                    text += key
                if echoing:
                    self._put(y,x,text+' '*(self.width-x-len(text)))
                    self.move(y,x+len(text))
        finally:
            self.echoing = echoing

    def refresh(self):
        info = self._info(self.output)
        self._require_size(info)
        x, y = info.srWindow.Left, info.srWindow.Top
        target = SMALL_RECT(x, y, x+self.width-1, y+self.height-1)
        _check(self.api.WriteConsoleOutputW(self.output, self.cells, COORD(self.width,self.height),
                                          COORD(0,0), ct.byref(target)), 'WriteConsoleOutputW')
        _check(self.api.SetConsoleCursorPosition(self.output, COORD(x+self.cursor_x,y+self.cursor_y)), "SetConsoleCursorPosition")
        # The API clips writes if the window/buffer shrank between the size check and write.
        if (target.Left,target.Top,target.Right,target.Bottom) != (x,y,x+self.width-1,y+self.height-1):
            raise error('Console resized while drawing. Restore at least 80x24 and restart Xonix.')

    def nodelay(self, flag):
        self.blocking = not flag

    def keypad(self, flag):
        pass  # ReadConsoleInputW already reports arrows as virtual key codes.

    def getch(self):
        self.refresh()  # curses refreshes pending prompt text before reading input.
        value = self._read_key()
        if self.echoing and self.last_text is not None:
            self.addstr(self.last_text)
        return value

    def _read_key(self):
        if self.repeats:
            self.repeats -= 1
            return self.repeat_key
        record, read = INPUT_RECORD(), DWORD()
        while True:
            if not self.blocking:
                available = DWORD()
                _check(self.api.GetNumberOfConsoleInputEvents(self.input, ct.byref(available)), 'GetNumberOfConsoleInputEvents')
                if not available.value:
                    self.last_text = None
                    return -1
            _check(self.api.ReadConsoleInputW(self.input, ct.byref(record), 1, ct.byref(read)), 'ReadConsoleInputW')
            if not read.value:
                continue
            value = _key(record)
            if value is not None:
                char = record.Event.KeyEvent.uChar.UnicodeChar
                self.last_text = ("\n" if char == 13 else chr(char)) if char and char not in (8,127) else None
                self.repeat_key = value
                self.repeats = max(0, record.Event.KeyEvent.wRepeatCount-1)
                return value

    def close(self, ignore_errors=False):
        failures = []
        # Attempt every restoration even if one native operation fails.
        if self.active:
            if not self.api.SetConsoleActiveScreenBuffer(self.original):
                failures.append('restore screen buffer')
            self.active = False
        if self.mode_saved:
            if not self.api.SetConsoleMode(self.input, self.original_mode.value):
                failures.append('restore console input mode')
            self.mode_saved = False
        if self.output is not None:
            if not self.api.CloseHandle(self.output):
                failures.append('close screen buffer')
            self.output = None
        if failures and not ignore_errors:
            raise error('Could not '+', '.join(failures)+'.')


def wrapper(function, *args, **kwargs):
    global _current_screen
    screen = Screen()
    _current_screen = screen
    try:
        result = function(screen, *args, **kwargs)
    except BaseException:
        screen.close(ignore_errors=True)
        raise
    else:
        screen.close()
        return result
    finally:
        _current_screen = None


def echo():
    _current_screen.echoing = True


def noecho():
    _current_screen.echoing = False


def curs_set(visible):
    cursor = CONSOLE_CURSOR_INFO(25, bool(visible))
    _check(_current_screen.api.SetConsoleCursorInfo(_current_screen.output, ct.byref(cursor)), "SetConsoleCursorInfo")


def napms(milliseconds):
    time.sleep(milliseconds / 1000)
