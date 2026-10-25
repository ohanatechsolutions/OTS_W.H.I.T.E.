"""Minimal local desktop interface using the Python standard-library Tk GUI."""
from __future__ import annotations
import queue
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .cli import audit
from .model import ScanReport
from .reporting import render


class AegisWhiteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aegis White | Ohana Tech")
        self.geometry("1040x670")
        self.minsize(820, 510)
        self.folder = tk.StringVar(value=str(Path.cwd()))
        self.history = tk.BooleanVar(value=False)
        self.include_sca = tk.BooleanVar(value=True)
        self.base = tk.StringVar()
        self.status = tk.StringVar(value="Select an authorized local repository to audit.")
        self.latest: ScanReport | None = None
        self.events: queue.Queue[ScanReport | Exception] = queue.Queue()
        self._create_widgets()
        self.after(100, self._poll)

    def _create_widgets(self):
        header = ttk.Frame(self, padding=(18, 14))
        header.pack(fill="x")
        ttk.Label(header, text="AEGIS WHITE", font=("Segoe UI", 23, "bold")).pack(anchor="w")
        ttk.Label(header, text="Private, local-first repository security auditing  •  Ohana Tech Solutions",
                  foreground="#687483").pack(anchor="w")
        path_row = ttk.Frame(self, padding=(18, 3))
        path_row.pack(fill="x")
        ttk.Label(path_row, text="Repository folder:").pack(side="left")
        ttk.Entry(path_row, textvariable=self.folder).pack(side="left", fill="x", expand=True, padx=10)
        ttk.Button(path_row, text="Browse…", command=self._browse).pack(side="left")

        controls = ttk.Frame(self, padding=(18, 10))
        controls.pack(fill="x")
        ttk.Checkbutton(controls, text="Scan Git history", variable=self.history).pack(side="left", padx=(0, 18))
        ttk.Checkbutton(controls, text="Offline dependency SCA (requires OSV database)",
                        variable=self.include_sca).pack(side="left", padx=(0, 18))
        ttk.Label(controls, text="PR base ref (optional):").pack(side="left")
        ttk.Entry(controls, textvariable=self.base, width=20).pack(side="left", padx=7)
        self.start_button = ttk.Button(controls, text="Run Audit", command=self._start)
        self.start_button.pack(side="right")

        toolbar = ttk.Frame(self, padding=(18, 4))
        toolbar.pack(fill="x")
        ttk.Label(toolbar, textvariable=self.status).pack(side="left", fill="x", expand=True)
        self.export_button = ttk.Button(toolbar, text="Export report…", command=self._export, state="disabled")
        self.export_button.pack(side="right")

        frame = ttk.Frame(self, padding=(18, 6))
        frame.pack(fill="both", expand=True)
        columns = ("severity", "category", "rule", "file", "line", "message")
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        self.tree = tree
        for key, title, width in (
            ("severity", "Severity", 85), ("category", "Type", 70), ("rule", "Rule", 165),
            ("file", "File", 240), ("line", "Line", 50), ("message", "Finding", 370)
        ):
            tree.heading(key, text=title)
            tree.column(key, width=width, minwidth=50 if key != "line" else 35, stretch=key in ("file", "message"))
        tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scroll.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scroll.set)
        tree.bind("<<TreeviewSelect>>", self._select)
        detail = ttk.LabelFrame(self, text="Remediation guidance", padding=12)
        detail.pack(fill="x", padx=18, pady=(5, 15))
        self.guidance = ttk.Label(detail, text="Select a finding to see recommendations.", wraplength=950)
        self.guidance.pack(anchor="w")

    def _browse(self):
        chosen = filedialog.askdirectory(title="Select local repository")
        if chosen:
            self.folder.set(chosen)

    def _start(self):
        folder = self.folder.get()
        if not Path(folder).is_dir():
            messagebox.showerror("Invalid folder", "Choose an existing repository folder.")
            return
        if not messagebox.askokcancel("Confirm authorized scan",
                                     "Only scan repositories you own or have permission to audit. Proceed?"):
            return
        self.start_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self.latest = None
        self.tree.delete(*self.tree.get_children())
        self.status.set("Auditing locally… No repository data is uploaded.")
        choices = (Path(folder).resolve(), self.history.get(), self.include_sca.get(), self.base.get().strip())
        def worker():
            try:
                result = audit(choices[0], history=choices[1], no_sca=not choices[2], base=choices[3] or None)
                self.events.put(result)
            except Exception as exc:
                # Never display source content or command stderr in unexpected error strings.
                self.events.put(exc)
        threading.Thread(target=worker, daemon=True).start()

    def _poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                self.start_button.configure(state="normal")
                if isinstance(event, Exception):
                    self.status.set("Audit interrupted; inspect local configuration and retry.")
                    messagebox.showerror("Audit error", "Audit interrupted. No source content was uploaded.")
                    continue
                self.latest = event
                self.export_button.configure(state="normal")
                for index, finding in enumerate(event.findings):
                    self.tree.insert("", "end", iid=str(index), values=(
                        finding.severity.upper(), finding.category, finding.rule_id,
                        finding.path, finding.line, finding.message))
                label = "Complete" if event.complete else "Incomplete / check prerequisites"
                self.status.set(f"{label} — {len(event.findings)} findings · {event.scanned_files} files · {event.scanned_history_blobs} historical blobs")
                if event.errors:
                    messagebox.showwarning("Audit incomplete", "\n".join(event.errors[:5]))
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self._poll)

    def _select(self, _event):
        selection = self.tree.selection()
        if selection and self.latest:
            finding = self.latest.findings[int(selection[0])]
            self.guidance.configure(text=f"{finding.recommendation}\n{finding.reference}")

    def _export(self):
        if self.latest is None:
            return
        filename = filedialog.asksaveasfilename(title="Export sanitized report", defaultextension=".json",
            filetypes=[("JSON audit", "*.json"), ("SARIF report", "*.sarif"), ("Plain text", "*.txt")])
        if not filename:
            return
        chosen = "sarif" if filename.endswith(".sarif") else "table" if filename.endswith(".txt") else "json"
        target = Path(filename)
        try:
            if target.is_symlink():
                raise OSError("refusing symlink")
            target.write_text(render(self.latest, chosen), encoding="utf-8")
            messagebox.showinfo("Report saved", "Sanitized report saved locally.")
        except OSError:
            messagebox.showerror("Save failed", "Unable to write report to the selected location.")


def main():
    try:
        AegisWhiteApp().mainloop()
    except tk.TclError:
        raise SystemExit("Unable to open the desktop GUI. Use 'python -m aegis_white' instead.")


if __name__ == "__main__":
    main()
