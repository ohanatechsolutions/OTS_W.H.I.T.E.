"""OTS W.H.I.T.E. desktop interface — dark steel-blue security dashboard.

Pure Tkinter (no web runtime or optional theme dependencies). Audit results are
always local, and this presentation layer never displays credential contents.
"""
from __future__ import annotations

import queue
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from .cli import audit
from .model import ScanReport
from .reporting import render


# Shared design tokens: slate surfaces, steel-blue highlights, soft white text.
BG = "#0F172A"
SURFACE = "#1E293B"
DEEP = "#111E31"
RAISED = "#26384D"
ACCENT = "#34587C"
ACCENT_DARK = "#24405E"
ACCENT_BRIGHT = "#4E79A7"
ICE = "#8BA8CD"
TEXT = "#FFFFFF"
MUTED = "#A5B6CC"
BORDER = "#33455B"  # Tk does not support rgba border colors or true blur.
SUCCESS = "#36C6A0"
WARNING = "#E7B66B"
DANGER = "#F18991"
FONT = "Segoe UI"


def asset_path(filename: str) -> Path:
    """Find icons in source installations and in PyInstaller one-file builds."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / "ots_white" / "assets" / filename


def fit_window_to_work_area(
    work_area: tuple[int, int, int, int],
    preferred: tuple[int, int] = (1300, 800),
    minimum: tuple[int, int] = (760, 560),
) -> tuple[str, tuple[int, int]]:
    """Return centered Tk geometry and achievable minimums within the usable screen."""
    x, y, work_width, work_height = work_area
    if work_width <= 0 or work_height <= 0:
        raise ValueError("The monitor work area must have positive dimensions.")
    # Leave space for window borders and avoid running beneath taskbars/docks.
    width = min(preferred[0], max(1, work_width - 32))
    height = min(preferred[1], max(1, work_height - 32))
    left = x + (work_width - width) // 2
    top = y + (work_height - height) // 2
    left_part = f"+{left}" if left >= 0 else str(left)
    top_part = f"+{top}" if top >= 0 else str(top)
    return f"{width}x{height}{left_part}{top_part}", (
        min(minimum[0], width), min(minimum[1], height)
    )


def _enable_windows_dpi_awareness() -> None:
    """Use physical monitor pixels in Tk when Windows supports per-monitor DPI."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        # Per-monitor DPI v2, falling back for older Windows versions.
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError, ValueError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def _work_area(window: tk.Tk) -> tuple[int, int, int, int]:
    """Read the actual monitor work area, excluding the Windows taskbar."""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class Rect(ctypes.Structure):
                _fields_ = [
                    ("left", wintypes.LONG), ("top", wintypes.LONG),
                    ("right", wintypes.LONG), ("bottom", wintypes.LONG),
                ]

            class MonitorInfo(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD), ("rcMonitor", Rect),
                    ("rcWork", Rect), ("dwFlags", wintypes.DWORD),
                ]

            user32 = ctypes.windll.user32
            user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
            user32.MonitorFromWindow.restype = wintypes.HANDLE
            user32.GetMonitorInfoW.argtypes = [
                wintypes.HANDLE, ctypes.POINTER(MonitorInfo)
            ]
            user32.GetMonitorInfoW.restype = wintypes.BOOL
            monitor = user32.MonitorFromWindow(window.winfo_id(), 2)
            info = MonitorInfo()
            info.cbSize = ctypes.sizeof(MonitorInfo)
            if monitor and user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                rect = info.rcWork
                return (
                    rect.left, rect.top,
                    rect.right - rect.left, rect.bottom - rect.top,
                )
        except (AttributeError, OSError, ValueError):
            pass
    return (window.winfo_vrootx(), window.winfo_vrooty(),
            window.winfo_screenwidth(), window.winfo_screenheight())


class OTSWhiteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OTS W.H.I.T.E.  |  Ohana Tech Solutions")
        self.configure(bg=BG)
        # Default to 1300 x 800; only shrink when the current work area is smaller.
        # Tk keeps its native DPI-aware font scaling for readable controls.
        geometry, minimum = fit_window_to_work_area(_work_area(self))
        self.geometry(geometry)
        self.minsize(*minimum)
        self.folder = tk.StringVar(value=str(Path.cwd()))
        self.history = tk.BooleanVar(value=False)
        self.include_sca = tk.BooleanVar(value=True)
        self.base = tk.StringVar()
        self.status = tk.StringVar(value="Ready to audit an authorized local repository")
        self.search = tk.StringVar()
        self.active_filter = "All"
        self.latest: ScanReport | None = None
        self.events: queue.Queue[ScanReport | Exception] = queue.Queue()
        self.visible_limit = 80
        self.filter_buttons: dict[str, tk.Button] = {}
        self.logo_image = None
        self.active_card = None
        self._load_icons()
        self._create_widgets()
        self.search.trace_add("write", lambda *_: self._refresh_findings(reset=True))
        self.after(100, self._poll)

    def _load_icons(self):
        ico = asset_path("ots_white.ico")
        png = asset_path("ots_white_logo.png")
        if png.exists():
            try:
                self.logo_image = tk.PhotoImage(file=str(png))
                self.iconphoto(True, self.logo_image)
            except tk.TclError:
                self.logo_image = None
        if ico.exists() and sys.platform == "win32":
            # Keep the native ICO as the Windows titlebar/taskbar icon.
            try:
                self.iconbitmap(default=str(ico))
            except tk.TclError:
                pass

    @staticmethod
    def _label(parent, text, size=10, color=TEXT, bold=False, **options):
        return tk.Label(parent, text=text, bg=parent.cget("bg"),
                        fg=color, font=(FONT, size, "bold" if bold else "normal"),
                        anchor="w", **options)

    @staticmethod
    def _surface(parent, bg=SURFACE, border=BORDER):
        return tk.Frame(parent, bg=bg, highlightbackground=border,
                        highlightcolor=border, highlightthickness=1, bd=0)

    @staticmethod
    def _button(parent, text, command, primary=False, width=None):
        opts = dict(bg=ACCENT if primary else SURFACE,
                    activebackground=ACCENT_BRIGHT if primary else RAISED,
                    fg=TEXT, activeforeground=TEXT,
                    relief="flat", bd=0, cursor="hand2", font=(FONT, 10, "bold"),
                    padx=16, pady=10, highlightthickness=1,
                    highlightbackground=ACCENT_BRIGHT if primary else BORDER)
        if width is not None:
            opts["width"] = width
        return tk.Button(parent, text=text, command=command, **opts)

    def _create_widgets(self):
        shell = tk.Frame(self, bg=BG)
        shell.pack(fill="both", expand=True)

        sidebar = tk.Frame(shell, bg=DEEP, width=225, highlightthickness=1,
                           highlightbackground=BORDER)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=DEEP)
        brand.pack(fill="x", padx=20, pady=(22, 25))
        if self.logo_image is not None:
            # Small, optimized PNG is suitable for the sidebar branding.
            tk.Label(brand, image=self.logo_image, bg=DEEP, bd=0).pack(anchor="w")
        self._label(brand, "OTS W.H.I.T.E.", 17, TEXT, True).pack(anchor="w", pady=(8, 4))
        self._label(brand, "WHITE HAT INFILTRATION\nTESTING ENGINE",
                    8, ICE, False, justify="left").pack(anchor="w")

        self._sidebar_link(sidebar, "◈    Dashboard", lambda: self._focus(self.folder_entry), True)
        self._sidebar_link(sidebar, "⌕    Repository Audit", lambda: self._focus(self.folder_entry))
        self._sidebar_link(sidebar, "▤    Findings", lambda: self._focus(self.search_entry))
        self._sidebar_link(sidebar, "⇧    Export Reports", self._export)
        self._label(sidebar, "LOCAL-FIRST SECURITY", 8, ICE, True).pack(
            anchor="w", padx=22, pady=(26, 6))
        self._label(sidebar, "Source code stays on this device.\nNo secrets are copied into reports.",
                    9, MUTED, False, justify="left").pack(anchor="w", padx=22)

        # The bottom branding is intentionally understated.
        tk.Label(sidebar, text="OHANA TECH SOLUTIONS", bg=DEEP, fg=MUTED,
                 font=(FONT, 8, "bold")).pack(side="bottom", anchor="w", padx=22, pady=22)

        # Allow the dashboard to scroll if high DPI or a small screen makes the
        # controls taller than the available client area. The findings list retains
        # its own independent scrollbar.
        workspace_shell = tk.Frame(shell, bg=BG)
        workspace_shell.pack(side="left", fill="both", expand=True)
        workspace_canvas = tk.Canvas(workspace_shell, bg=BG, bd=0,
                                     highlightthickness=0)
        workspace_canvas.pack(side="left", fill="both", expand=True)
        workspace_scrollbar = tk.Scrollbar(workspace_shell, orient="vertical",
                                           command=workspace_canvas.yview,
                                           bg=SURFACE, troughcolor=DEEP)
        workspace_canvas.configure(yscrollcommand=workspace_scrollbar.set)
        workspace = tk.Frame(workspace_canvas, bg=BG)
        workspace_window = workspace_canvas.create_window(
            (0, 0), window=workspace, anchor="nw")

        def resize_workspace(_event=None):
            needed = workspace.winfo_reqheight()
            visible = workspace_canvas.winfo_height()
            workspace_canvas.itemconfigure(
                workspace_window, width=workspace_canvas.winfo_width(),
                height=max(needed, visible))
            workspace_canvas.configure(scrollregion=workspace_canvas.bbox("all"))
            if needed > visible + 2 and not workspace_scrollbar.winfo_manager():
                workspace_scrollbar.pack(side="right", fill="y")
            elif needed <= visible + 2 and workspace_scrollbar.winfo_manager():
                workspace_scrollbar.pack_forget()

        workspace.bind("<Configure>", resize_workspace)
        workspace_canvas.bind("<Configure>", resize_workspace)

        top = tk.Frame(workspace, bg=BG)
        top.pack(fill="x", padx=24, pady=(22, 16))
        titles = tk.Frame(top, bg=BG)
        titles.pack(side="left", fill="x", expand=True)
        self._label(titles, "Security Overview", 24, TEXT, True).pack(anchor="w")
        self._label(titles, "Audit your repositories with a private, local-first workflow",
                    10, MUTED).pack(anchor="w", pady=(4, 0))
        self._button(top, "Export sanitized report", self._export).pack(side="right", pady=7)
        self.export_button = top.winfo_children()[-1]
        self.export_button.configure(state="disabled")

        config = self._surface(workspace)
        config.pack(fill="x", padx=24, pady=(0, 16))
        fields = tk.Frame(config, bg=SURFACE)
        fields.pack(fill="x", padx=17, pady=(16, 10))
        self._label(fields, "REPOSITORY LOCATION", 9, ICE, True).pack(anchor="w", pady=(0, 8))
        pathline = tk.Frame(fields, bg=SURFACE)
        pathline.pack(fill="x")
        self.folder_entry = self._entry(pathline, self.folder)
        self.folder_entry.pack(side="left", fill="x", expand=True)
        self._button(pathline, "Browse…", self._browse).pack(side="left", padx=(9, 0))
        controls = tk.Frame(config, bg=SURFACE)
        controls.pack(fill="x", padx=17, pady=(3, 14))
        # Separate rows keep the actions visible on narrower laptop screens.
        options_row = tk.Frame(controls, bg=SURFACE)
        options_row.pack(fill="x")
        self._check(options_row, "Git history", self.history).pack(side="left", padx=(0, 16))
        self._check(options_row, "Offline dependency SCA (OSV required)", self.include_sca).pack(
            side="left")
        actions_row = tk.Frame(controls, bg=SURFACE)
        actions_row.pack(fill="x", pady=(6, 0))
        self._label(actions_row, "PR base:", 9, MUTED).pack(side="left")
        self._entry(actions_row, self.base, width=13).pack(side="left", padx=(8, 10))
        self.start_button = self._button(actions_row, "Run Audit", self._start, primary=True)
        self.start_button.pack(side="right")

        metricline = tk.Frame(workspace, bg=BG)
        metricline.pack(fill="x", padx=24, pady=(0, 14))
        self.metric_total = self._metric(metricline, "FINDINGS", "0")
        self.metric_high = self._metric(metricline, "HIGH / CRITICAL", "0")
        self.metric_files = self._metric(metricline, "FILES SCANNED", "0")
        self.metric_history = self._metric(metricline, "HISTORY BLOBS", "0")

        statusbar = self._surface(workspace, bg=DEEP)
        statusbar.pack(fill="x", padx=24, pady=(0, 14))
        tk.Label(statusbar, text="●", bg=DEEP, fg=SUCCESS,
                 font=(FONT, 12)).pack(side="left", padx=(14, 6), pady=9)
        tk.Label(statusbar, textvariable=self.status, bg=DEEP, fg=ICE,
                 font=(FONT, 9), anchor="w").pack(side="left", fill="x", expand=True)
        self._label(statusbar, "OFFLINE · PRIVATE", 8, MUTED, True).pack(
            side="right", padx=14)

        body = tk.Frame(workspace, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 22))

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)
        filters = tk.Frame(left, bg=BG)
        filters.pack(fill="x", pady=(0, 10))
        self._label(filters, "Audit Findings", 16, TEXT, True).pack(side="left")
        chips = tk.Frame(filters, bg=BG)
        chips.pack(side="right")
        for name in ("All", "Secrets", "SAST", "Dependencies"):
            btn = self._button(chips, name, lambda n=name: self._set_filter(n))
            btn.pack(side="left", padx=(5, 0))
            self.filter_buttons[name] = btn
        self._update_filters()

        searchframe = self._surface(left, bg=DEEP, border=ACCENT)
        searchframe.pack(fill="x", pady=(0, 10))
        tk.Label(searchframe, text="⌕", bg=DEEP, fg=ICE,
                 font=(FONT, 16)).pack(side="left", padx=(12, 6), pady=6)
        self.search_entry = self._entry(searchframe, self.search, bg=DEEP)
        self.search_entry.pack(side="left", fill="x", expand=True, pady=6, padx=(0, 10))
        self.search_entry.configure(insertbackground=ICE)

        listwrap = self._surface(left, bg=DEEP)
        listwrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(listwrap, bg=DEEP, borderwidth=0,
                                highlightthickness=0, yscrollincrement=36)
        scrollbar = tk.Scrollbar(listwrap, orient="vertical", command=self.canvas.yview,
                                 bg=SURFACE, troughcolor=DEEP)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.feed = tk.Frame(self.canvas, bg=DEEP)
        self.feed_window = self.canvas.create_window((0, 0), window=self.feed, anchor="nw")
        self.feed.bind("<Configure>", lambda _event: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(
            self.feed_window, width=event.width))
        self.canvas.bind("<MouseWheel>", self._mousewheel)
        self.feed.bind("<MouseWheel>", self._mousewheel)

        right = self._surface(body, bg=DEEP)
        right.pack(side="left", fill="y", padx=(14, 0))
        right.configure(width=265)
        right.pack_propagate(False)
        self._label(right, "REMEDIATION GUIDANCE", 9, ICE, True).pack(
            anchor="w", padx=16, pady=(18, 12))
        self._label(right, "Finding details", 15, TEXT, True).pack(
            anchor="w", padx=16, pady=(0, 7))
        self.guidance = tk.Label(right, text="Select a finding to review its recommendation.",
                                  bg=DEEP, fg=MUTED, justify="left", anchor="nw",
                                  font=(FONT, 10), wraplength=225)
        self.guidance.pack(anchor="w", fill="x", padx=16, pady=(0, 16))
        line = tk.Frame(right, bg=BORDER, height=1)
        line.pack(fill="x", padx=16, pady=12)
        self._label(right, "Privacy by design", 10, TEXT, True).pack(
            anchor="w", padx=16, pady=(2, 6))
        self._label(right,
                    "Only rule IDs, paths and safe remediation guidance appear here. "
                    "Raw credentials never appear in findings.",
                    9, MUTED, justify="left", wraplength=225).pack(
                        anchor="w", padx=16)
        self._refresh_findings(reset=True)

    def _sidebar_link(self, parent, title, action, active=False):
        button = self._button(parent, title, action, primary=active)
        button.configure(anchor="w", padx=20)
        button.pack(fill="x", padx=12, pady=4)

    def _focus(self, widget):
        widget.focus_set()

    def _entry(self, parent, variable, width=None, bg=DEEP):
        options = dict(textvariable=variable, bg=bg, fg=TEXT,
                       insertbackground=ICE, relief="flat", bd=0,
                       highlightthickness=0, font=(FONT, 10))
        if width is not None:
            options["width"] = width
        entry = tk.Entry(parent, **options)
        return entry

    def _check(self, parent, text, variable):
        return tk.Checkbutton(parent, text=text, variable=variable, bg=SURFACE, fg=TEXT,
                              selectcolor=ACCENT_DARK, activebackground=SURFACE,
                              activeforeground=TEXT, font=(FONT, 9), bd=0,
                              cursor="hand2", highlightthickness=0)

    def _metric(self, parent, title, value):
        outer = self._surface(parent, bg=SURFACE)
        outer.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._label(outer, title, 8, ICE, True).pack(anchor="w", padx=14, pady=(12, 4))
        var = tk.StringVar(value=value)
        tk.Label(outer, textvariable=var, bg=SURFACE, fg=TEXT,
                 font=(FONT, 21, "bold")).pack(anchor="w", padx=14, pady=(0, 11))
        return var

    def _set_filter(self, name):
        self.active_filter = name
        self._update_filters()
        self._refresh_findings(reset=True)

    def _update_filters(self):
        for name, button in self.filter_buttons.items():
            button.configure(bg=ACCENT if name == self.active_filter else DEEP,
                             highlightbackground=ACCENT_BRIGHT if name == self.active_filter else BORDER)

    def _mousewheel(self, event):
        self.canvas.yview_scroll(-int(event.delta / 120), "units")

    def _visible_findings(self):
        if self.latest is None:
            return []
        term = self.search.get().strip().lower()
        category = {"Secrets": "secret", "SAST": "sast",
                    "Dependencies": "sca"}.get(self.active_filter)
        found = []
        for finding in self.latest.findings:
            if category and finding.category.lower() != category:
                continue
            searchable = " ".join((finding.rule_id, finding.path, finding.category,
                                   finding.severity, finding.message)).lower()
            if term and term not in searchable:
                continue
            found.append(finding)
        return found

    def _refresh_findings(self, reset=False):
        if not hasattr(self, "feed"):
            return
        if reset:
            self.visible_limit = 80
        for child in self.feed.winfo_children():
            child.destroy()
        self.active_card = None
        findings = self._visible_findings()
        if not findings:
            msg = ("Run a local repository audit to populate this view."
                   if self.latest is None else "No findings match the current filters.")
            self._label(self.feed, msg, 11, MUTED, justify="left").pack(
                anchor="w", padx=22, pady=28)
            return
        for finding in findings[:self.visible_limit]:
            self._finding_card(finding)
        if len(findings) > self.visible_limit:
            self._button(self.feed, f"Show more ({len(findings) - self.visible_limit} remaining)",
                         self._show_more).pack(fill="x", padx=10, pady=12)

    def _show_more(self):
        self.visible_limit += 80
        self._refresh_findings()

    def _finding_card(self, finding):
        card = self._surface(self.feed, bg=SURFACE)
        card.pack(fill="x", padx=10, pady=(8, 2))
        upper = tk.Frame(card, bg=SURFACE)
        upper.pack(fill="x", padx=14, pady=(12, 5))
        level = finding.severity.upper()
        tone = DANGER if level in ("CRITICAL", "HIGH") else WARNING if level == "MEDIUM" else ICE
        tk.Label(upper, text=level, bg=ACCENT_DARK, fg=tone,
                 font=(FONT, 8, "bold"), padx=8, pady=3).pack(side="left")
        tk.Label(upper, text=finding.category.upper(), bg=DEEP, fg=ICE,
                 font=(FONT, 8, "bold"), padx=8, pady=3).pack(side="left", padx=7)
        tk.Label(upper, text=finding.rule_id, bg=SURFACE, fg=TEXT,
                 font=(FONT, 10, "bold")).pack(side="left", padx=5)
        location = f"{finding.path}:{finding.line}"
        tk.Label(card, text=location, bg=SURFACE, fg=ICE,
                 font=(FONT, 9), anchor="w").pack(fill="x", padx=14, pady=(0, 3))
        tk.Label(card, text=finding.message, bg=SURFACE, fg=MUTED, anchor="w",
                 justify="left", wraplength=440, font=(FONT, 9)).pack(
                     fill="x", padx=14, pady=(0, 13))
        for widget in (card, upper, *upper.winfo_children(), *card.winfo_children()):
            widget.bind("<Button-1>", lambda _evt, f=finding, c=card: self._select(f, c))
            widget.bind("<MouseWheel>", self._mousewheel)

    def _select(self, finding, card):
        if self.active_card is not None and self.active_card.winfo_exists():
            self.active_card.configure(highlightbackground=BORDER)
        self.active_card = card
        card.configure(highlightbackground=ACCENT_BRIGHT)
        guidance = finding.recommendation or "Review and remediate this finding."
        reference = f"\n\nReference: {finding.reference}" if finding.reference else ""
        self.guidance.configure(text=f"{finding.rule_id}\n\n{guidance}{reference}")

    def _browse(self):
        chosen = filedialog.askdirectory(title="Select an authorized local repository")
        if chosen:
            self.folder.set(chosen)

    def _start(self):
        folder = self.folder.get()
        if not Path(folder).is_dir():
            messagebox.showerror("Invalid folder", "Choose an existing repository folder.")
            return
        if not messagebox.askokcancel(
                "Confirm authorized scan",
                "Only scan repositories you own or have permission to audit. Proceed?"):
            return
        self.start_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self.latest = None
        self._refresh_findings(reset=True)
        self.status.set("Auditing locally… No repository data is uploaded.")
        choices = (Path(folder).resolve(), self.history.get(),
                   self.include_sca.get(), self.base.get().strip())

        def worker():
            try:
                result = audit(choices[0], history=choices[1],
                               no_sca=not choices[2], base=choices[3] or None)
                self.events.put(result)
            except Exception:
                # Avoid exposing source snippets or process stderr in exception strings.
                self.events.put(RuntimeError("Audit interrupted"))

        threading.Thread(target=worker, daemon=True).start()

    def _poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                self.start_button.configure(state="normal")
                if isinstance(event, Exception):
                    self.status.set("Audit interrupted; check local configuration and retry.")
                    messagebox.showerror("Audit error", "Audit interrupted. No source content was uploaded.")
                    continue
                self.latest = event
                self.export_button.configure(state="normal")
                self.metric_total.set(str(len(event.findings)))
                self.metric_high.set(str(sum(
                    f.severity.lower() in ("critical", "high") for f in event.findings)))
                self.metric_files.set(str(event.scanned_files))
                self.metric_history.set(str(event.scanned_history_blobs))
                status = "Complete" if event.complete else "Incomplete — review prerequisites"
                self.status.set(f"{status} · {len(event.findings)} findings · {event.scanned_files} files")
                self._refresh_findings(reset=True)
                if event.errors:
                    messagebox.showwarning("Audit incomplete", "\n".join(event.errors[:5]))
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self._poll)

    def _export(self):
        if self.latest is None:
            return
        filename = filedialog.asksaveasfilename(
            title="Export sanitized report", defaultextension=".json",
            filetypes=[("JSON audit", "*.json"), ("SARIF report", "*.sarif"),
                       ("Plain text", "*.txt")])
        if not filename:
            return
        choice = "sarif" if filename.endswith(".sarif") else "table" if filename.endswith(".txt") else "json"
        target = Path(filename)
        try:
            if target.is_symlink():
                raise OSError("Refusing to follow symlink")
            target.write_text(render(self.latest, choice), encoding="utf-8")
            messagebox.showinfo("Report saved", "Sanitized report saved locally.")
        except OSError:
            messagebox.showerror("Save failed", "Unable to write report to the selected location.")


def main():
    _enable_windows_dpi_awareness()
    try:
        OTSWhiteApp().mainloop()
    except tk.TclError:
        raise SystemExit("Unable to open the desktop GUI. Use 'python -m ots_white' instead.")


if __name__ == "__main__":
    main()
