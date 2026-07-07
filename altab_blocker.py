"""AlTab Blocker — 선택한 프로그램 포커스 중 Alt+Tab 창 전환 차단.

동작 원리: 저수준 키보드 훅(WH_KEYBOARD_LL)으로 "Alt가 눌린 상태의 Tab 키 다운"
이벤트만 삼켜서 Windows 창 전환을 막는다. 그 외 모든 키 입력은 손대지 않고
그대로 통과시키며, 입력 주입(SendInput 등)은 일절 하지 않는다.
"""

import ctypes
import ctypes.wintypes as wt
import os
import sys
import threading
import tkinter as tk

import customtkinter as ctk
import psutil

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_QUIT = 0x0012
VK_TAB = 0x09
LLKHF_ALTDOWN = 0x20

ULONG_PTR = ctypes.c_size_t
LRESULT = ctypes.c_ssize_t

HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wt.WPARAM, wt.LPARAM)


def get_resource_path(relative: str) -> str:
    """PyInstaller onefile 실행 시 임시 해제 경로(_MEIPASS) 기준으로 리소스 탐색."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


APP_FONT_FAMILY = "Pretendard"
FONT_FILES = ["Pretendard-Regular.ttf", "Pretendard-Bold.ttf"]
FR_PRIVATE = 0x10


def register_app_fonts():
    """번들된 Pretendard를 AddFontResourceExW(FR_PRIVATE)로 프로세스 동안만
    등록하고(시스템 미설치), CTkFont 기본 패밀리를 Pretendard로 강제한다.
    CTkFont 생성 전(위젯 생성 전)에 호출해야 한다."""
    registered = 0
    try:
        gdi32 = ctypes.WinDLL("gdi32")
        for name in FONT_FILES:
            path = get_resource_path(os.path.join("assets", name))
            if os.path.exists(path) and gdi32.AddFontResourceExW(path, FR_PRIVATE, 0) > 0:
                registered += 1
    except OSError:
        pass
    if not registered:
        return  # 폰트 없으면 기본 폰트 유지

    # ThemeManager 갱신 — 명시적 font 없는 위젯의 기본 폰트에 적용
    try:
        from customtkinter.windows.widgets.theme import ThemeManager
        ThemeManager.theme["CTkFont"]["family"] = APP_FONT_FAMILY
    except Exception:
        pass

    # CTkFont.__init__ wrap — family 미지정 시 Pretendard 주입
    orig_init = ctk.CTkFont.__init__

    def patched_init(self, *args, **kwargs):
        if not args and "family" not in kwargs:
            kwargs["family"] = APP_FONT_FAMILY
        orig_init(self, *args, **kwargs)

    ctk.CTkFont.__init__ = patched_init

# 64비트에서 핸들 잘림 방지를 위한 시그니처 지정
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.SetWindowsHookExW.argtypes = (ctypes.c_int, HOOKPROC, ctypes.c_void_p, wt.DWORD)
user32.CallNextHookEx.restype = LRESULT
user32.CallNextHookEx.argtypes = (ctypes.c_void_p, ctypes.c_int, wt.WPARAM, wt.LPARAM)
user32.UnhookWindowsHookEx.argtypes = (ctypes.c_void_p,)
kernel32.GetModuleHandleW.restype = ctypes.c_void_p


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wt.DWORD),
        ("scanCode", wt.DWORD),
        ("flags", wt.DWORD),
        ("time", wt.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


def foreground_process_name() -> str:
    """현재 포커싱된 창의 프로세스 이름 (실패 시 빈 문자열)."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    try:
        return psutil.Process(pid.value).name()
    except psutil.Error:
        return ""


def list_window_processes() -> list[str]:
    """보이는 창을 가진 프로세스 이름 목록."""
    pids = set()

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def enum_cb(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd) > 0:
            pid = wt.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            pids.add(pid.value)
        return True

    user32.EnumWindows(enum_cb, 0)
    names = set()
    for pid in pids:
        try:
            names.add(psutil.Process(pid).name())
        except psutil.Error:
            pass
    return sorted(names, key=str.lower)


class Tooltip:
    """고DPI 안전 툴팁. winfo_screenwidth(논리)에 window_scaling을 곱해
    rootx/geometry(물리)와 좌표계를 통일해 클램프하고, withdraw로 위치 확정 후
    표시한다(고DPI에서 overrideredirect 위치 무시 방지)."""

    def __init__(self, widget, text, font=None):
        self.widget = widget
        self.text = text
        self.font = font
        self.tip = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<Destroy>", self._hide, add="+")

    def _show(self, _e=None):
        if self.tip or not self.text:
            return
        self.tip = tk.Toplevel(self.widget)
        self.tip.withdraw()
        self.tip.wm_overrideredirect(True)
        lbl = tk.Label(self.tip, text=self.text, bg="#11151c", fg="#e6eaee",
                       justify="left", wraplength=420, padx=10, pady=7,
                       bd=1, relief="solid", highlightbackground="#3a4250")
        if self.font:
            lbl.configure(font=self.font)
        lbl.pack()
        self.tip.update_idletasks()
        try:
            wsc = ctk.ScalingTracker.get_window_scaling(self.widget)
        except Exception:
            wsc = 1.0
        tw, th = self.tip.winfo_reqwidth(), self.tip.winfo_reqheight()
        sw = round(self.widget.winfo_screenwidth() * wsc)
        sh = round(self.widget.winfo_screenheight() * wsc)
        wx, wy = self.widget.winfo_rootx(), self.widget.winfo_rooty()
        ww, wh = self.widget.winfo_width(), self.widget.winfo_height()
        x = max(8, min(wx + ww // 2 - tw // 2, sw - tw - 8))
        bottom = round(56 * wsc)  # 작업표시줄 여백
        below_y = wy + wh + 4
        above_y = wy - th - 4
        y = below_y if below_y + th <= sh - bottom else max(8, above_y)
        y = max(8, min(y, sh - th - bottom))
        self.tip.wm_geometry(f"+{int(x)}+{int(y)}")
        self.tip.deiconify()

    def _hide(self, _e=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class KeyboardHook:
    """차단 전용 저수준 키보드 훅. should_block()이 True를 반환하는 순간의
    Alt+Tab(Tab 다운)만 삼키고, 나머지는 전부 다음 훅으로 통과."""

    def __init__(self, should_block, on_block):
        self._should_block = should_block
        self._on_block = on_block
        self._proc = HOOKPROC(self._callback)  # GC 방지를 위해 참조 유지
        self._thread = None
        self._thread_id = None
        self._started = threading.Event()
        self._install_ok = False

    def _callback(self, n_code, w_param, l_param):
        if n_code == 0 and w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
            kb = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if kb.vkCode == VK_TAB and kb.flags & LLKHF_ALTDOWN and self._should_block():
                self._on_block()
                return 1  # 이 Tab 다운만 삼킴 → 창 전환 차단
        return user32.CallNextHookEx(None, n_code, w_param, l_param)

    def _run(self):
        self._thread_id = kernel32.GetCurrentThreadId()
        hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._proc, kernel32.GetModuleHandleW(None), 0
        )
        self._install_ok = bool(hook)
        self._started.set()
        if not hook:
            return
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            pass
        user32.UnhookWindowsHookEx(hook)

    def start(self) -> bool:
        """훅 설치. 성공 여부 반환."""
        if self._thread and self._thread.is_alive():
            return self._install_ok
        self._started.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._started.wait(timeout=3)
        return self._install_ok

    def stop(self):
        if self._thread and self._thread.is_alive():
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            self._thread.join(timeout=3)
        self._thread = None


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AlTab Blocker")
        self.geometry("390x380")
        self.resizable(False, False)
        self._apply_window_icon()

        self.blocked_count = 0
        self.hook = KeyboardHook(self._should_block, self._on_block)

        pad = {"padx": 16, "pady": (12, 0)}
        base_font = ctk.CTkFont(size=16)

        self.switch = ctk.CTkSwitch(
            self, text="Alt+Tab 차단", font=ctk.CTkFont(size=19, weight="bold"),
            command=self._on_toggle,
        )
        self.switch.pack(anchor="w", **pad)

        self.mode = ctk.CTkSegmentedButton(
            self, values=["선택 프로그램에서만", "전역 차단"], font=base_font,
            command=lambda _v: self._update_status(),
        )
        self.mode.set("선택 프로그램에서만")
        self.mode.pack(fill="x", **pad)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", **pad)
        self.process_box = ctk.CTkComboBox(
            row, values=[""], font=base_font, dropdown_font=base_font,
            command=lambda _v: self._update_status(),
        )
        self.process_box.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="새로고침", width=80, font=base_font,
                      command=self._refresh_processes).pack(side="left", padx=(8, 0))

        self.status = ctk.CTkLabel(self, text="", justify="left", wraplength=350,
                                   font=base_font)
        self.status.pack(anchor="w", **pad)

        self.counter = ctk.CTkLabel(self, text="차단된 Alt+Tab: 0회", text_color="gray",
                                    font=ctk.CTkFont(size=14))
        self.counter.pack(anchor="w", padx=16, pady=(4, 0))

        if not self._is_admin():
            help_row = ctk.CTkFrame(self, fg_color="transparent")
            help_row.pack(anchor="w", padx=16, pady=(12, 0))
            ctk.CTkLabel(help_row, text="작동이 안 된다면",
                         font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
            help_btn = ctk.CTkButton(help_row, text="?", width=30, height=30,
                                     corner_radius=15, font=ctk.CTkFont(size=16, weight="bold"))
            help_btn.pack(side="left", padx=(8, 0))
            Tooltip(help_btn,
                    "이 프로그램을 종료한 뒤,\n"
                    "우클릭 → '관리자 권한으로 실행'으로 다시 실행하세요.",
                    font=ctk.CTkFont(size=15))

        self._refresh_processes()
        self._update_status()
        self._poll()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_window_icon(self):
        """타이틀바 + 작업표시줄 아이콘. ICO 안의 모든 사이즈를 iconphoto로 등록
        (작업표시줄 흐림 방지) + iconbitmap을 fallback으로 항상 호출.
        icon.ico가 없으면 조용히 건너뛴다. PhotoImage는 self에 보관(GC 방지)."""
        icon_path = get_resource_path(os.path.join("assets", "icon.ico"))
        if not os.path.exists(icon_path):
            return

        try:
            self.iconbitmap(default=icon_path)
        except Exception:
            pass

        try:
            from PIL import Image, ImageTk
            with Image.open(icon_path) as ico:
                if hasattr(ico, "ico"):
                    imgs = []
                    for s in sorted(ico.ico.sizes()):
                        sub = ico.ico.getimage(s)
                        sub.load()
                        imgs.append(sub.copy())
                else:
                    ico.load()
                    imgs = [ico.copy()]
            self._icon_photos = [ImageTk.PhotoImage(im) for im in imgs]
            self.iconphoto(True, *self._icon_photos)
        except Exception:
            pass

    @staticmethod
    def _is_admin() -> bool:
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except OSError:
            return False

    # ── 훅 콜백 (훅 스레드에서 호출됨) ──────────────────────────────
    def _should_block(self) -> bool:
        if self.mode.get() == "전역 차단":
            return True
        target = self.process_box.get().strip()
        return bool(target) and foreground_process_name().lower() == target.lower()

    def _on_block(self):
        self.blocked_count += 1

    # ── GUI ────────────────────────────────────────────────────────
    def _on_toggle(self):
        if self.switch.get():
            if not self.hook.start():
                self.switch.deselect()
                self.status.configure(text="⚠ 훅 설치 실패 — 관리자 권한으로 다시 실행해보세요.")
                return
        else:
            self.hook.stop()
        self._update_status()

    def _refresh_processes(self):
        names = list_window_processes()
        self.process_box.configure(values=names)
        current = self.process_box.get().strip()
        if not current or current not in names:
            maple = next((n for n in names if "maplestory" in n.lower()), None)
            self.process_box.set(maple or (names[0] if names else ""))
        self._update_status()

    def _update_status(self):
        if not self.switch.get():
            self.status.configure(text="⏸ 꺼짐 — Alt+Tab 정상 작동")
        elif self.mode.get() == "전역 차단":
            self.status.configure(text="🛡 전역 차단 중 — 모든 창에서 Alt+Tab 무시")
        else:
            target = self.process_box.get().strip() or "(프로세스 미선택)"
            self.status.configure(text=f"🛡 {target} 포커스 중에만 Alt+Tab 무시")

    def _poll(self):
        self.counter.configure(text=f"차단된 Alt+Tab: {self.blocked_count}회")
        self.after(500, self._poll)

    def _on_close(self):
        self.hook.stop()
        self.destroy()


if __name__ == "__main__":
    try:  # 작업표시줄에서 python 기본 아이콘 대신 앱 고유 아이콘이 나오도록 분리
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.altablocker.app")
    except Exception:
        pass
    ctk.set_appearance_mode("system")
    register_app_fonts()
    App().mainloop()
