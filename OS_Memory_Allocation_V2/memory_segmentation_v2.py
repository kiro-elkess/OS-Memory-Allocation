"""
Memory Allocation Simulator — Segmentation  (v2)
=================================================
Same functionality as v1, completely redesigned UI.
Light theme, sidebar layout, rounded accents.

Run:   python memory_segmentation_v2.py
Build: python -m PyInstaller --onefile --windowed memory_segmentation_v2.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math

# ─────────────────────────────────────────────
#  PALETTE  (light / warm theme)
# ─────────────────────────────────────────────
BG        = "#F5F0EB"      # warm off-white background
SIDEBAR   = "#2B2D42"      # deep navy sidebar
CARD      = "#FFFFFF"      # white cards
CARD2     = "#EEE8E0"      # slightly darker card
BORDER    = "#D6CEC4"      # soft border
TEXT      = "#1A1A2E"      # near-black text
TEXT_LIGHT= "#FFFFFF"      # white text (on sidebar)
MUTED     = "#7A7A8C"      # muted label
ACCENT    = "#EF233C"      # vivid red accent
ACCENT2   = "#8D99AE"      # slate blue accent
SUCCESS   = "#2EC4B6"      # teal success
WARNING   = "#FF9F1C"      # amber warning
DANGER    = "#EF233C"      # red danger

PROCESS_COLORS = [
    "#EF233C", "#2EC4B6", "#FF9F1C", "#8338EC",
    "#06D6A0", "#FB5607", "#3A86FF", "#FFBE0B",
    "#8D99AE", "#E63946",
]

FONT_TITLE  = ("Segoe UI", 14, "bold")
FONT_HEAD   = ("Segoe UI", 11, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10)
FONT_MONO_S = ("Consolas", 9)
FONT_MONO_B = ("Consolas", 10, "bold")


# ─────────────────────────────────────────────
#  DATA MODEL  (identical logic to v1)
# ─────────────────────────────────────────────
class MemoryManager:
    def __init__(self, total_size):
        self.total_size = total_size
        self.holes = []
        self.allocated = []
        self.segment_tables = {}
        self.proc_colors = {}
        self._color_idx = 0

    def add_hole(self, start, size):
        self.holes.append({"start": start, "size": size})
        self._merge_holes()

    def _merge_holes(self):
        self.holes.sort(key=lambda h: h["start"])
        merged = []
        for h in self.holes:
            if merged and merged[-1]["start"] + merged[-1]["size"] == h["start"]:
                merged[-1]["size"] += h["size"]
            else:
                merged.append(dict(h))
        self.holes = merged

    def _get_color(self, proc_name):
        if proc_name not in self.proc_colors:
            self.proc_colors[proc_name] = PROCESS_COLORS[self._color_idx % len(PROCESS_COLORS)]
            self._color_idx += 1
        return self.proc_colors[proc_name]

    def allocate(self, proc_name, segments, method="first_fit"):
        if proc_name in self.segment_tables:
            return False, f"Process {proc_name} is already allocated."

        assignments = []
        temp_holes = [dict(h) for h in self.holes]

        for seg_name, seg_size in segments:
            chosen = None
            chosen_idx = -1

            if method == "first_fit":
                for i, h in enumerate(temp_holes):
                    if h["size"] >= seg_size:
                        chosen = h
                        chosen_idx = i
                        break
            else:
                best_waste = math.inf
                for i, h in enumerate(temp_holes):
                    waste = h["size"] - seg_size
                    if 0 <= waste < best_waste:
                        best_waste = waste
                        chosen = h
                        chosen_idx = i

            if chosen is None:
                return False, (
                    f"Process {proc_name} cannot be allocated — "
                    f"segment '{seg_name}' ({seg_size} KB) does not fit in any hole."
                )

            assignments.append((seg_name, seg_size, chosen_idx, chosen["start"]))
            temp_holes[chosen_idx]["start"] += seg_size
            temp_holes[chosen_idx]["size"]  -= seg_size

        self.holes = temp_holes
        self._merge_holes()

        color = self._get_color(proc_name)
        table = []
        for seg_name, seg_size, _, base in assignments:
            self.allocated.append({
                "start": base, "size": seg_size,
                "process": proc_name, "segment": seg_name,
                "color": color,
            })
            table.append({"segment": seg_name, "base": base, "limit": seg_size})

        self.segment_tables[proc_name] = table
        return True, f"Process {proc_name} allocated successfully."

    def deallocate(self, proc_name):
        if proc_name not in self.segment_tables:
            return False, f"Process {proc_name} is not allocated."

        freed = [a for a in self.allocated if a["process"] == proc_name]
        self.allocated = [a for a in self.allocated if a["process"] != proc_name]

        for seg in freed:
            self.holes.append({"start": seg["start"], "size": seg["size"]})

        self._merge_holes()
        del self.segment_tables[proc_name]
        del self.proc_colors[proc_name]

        return True, f"Process {proc_name} deallocated. {len(freed)} segment(s) freed."

    def memory_map(self):
        regions = []
        for a in self.allocated:
            regions.append({**a, "type": "allocated"})
        for h in self.holes:
            regions.append({"start": h["start"], "size": h["size"], "type": "hole"})
        regions.sort(key=lambda r: r["start"])

        filled = []
        cursor = 0
        for r in regions:
            if r["start"] > cursor:
                filled.append({"start": cursor, "size": r["start"] - cursor, "type": "uninitialized"})
            filled.append(r)
            cursor = r["start"] + r["size"]
        if cursor < self.total_size:
            filled.append({"start": cursor, "size": self.total_size - cursor, "type": "uninitialized"})
        return filled


# ─────────────────────────────────────────────
#  SETUP DIALOG
# ─────────────────────────────────────────────
class SetupDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.transient(parent)
        self.title("Initialize Memory")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.result = None
        self._build()
        self.grab_set()
        self.wait_window()

    def _build(self):
        # Header strip
        hdr = tk.Frame(self, bg=SIDEBAR, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  Initialize Memory", font=FONT_TITLE,
                 bg=SIDEBAR, fg=TEXT_LIGHT).pack(side="left", padx=16, pady=12)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        # Total size
        tk.Label(body, text="Total memory size (KB)", font=FONT_BODY,
                 bg=BG, fg=MUTED).grid(row=0, column=0, sticky="w", pady=(0,4))
        self.total_var = tk.StringVar(value="1024")
        self._entry(body, self.total_var, width=12).grid(row=1, column=0, sticky="w", pady=(0,14))

        # Holes
        tk.Label(body, text="Free holes  (start, size — one per line)",
                 font=FONT_BODY, bg=BG, fg=MUTED).grid(row=2, column=0, sticky="w", pady=(0,4))
        self.holes_text = tk.Text(body, font=FONT_MONO, bg=CARD, fg=TEXT,
                                  relief="flat", width=28, height=5,
                                  highlightthickness=1, highlightbackground=BORDER,
                                  highlightcolor=ACCENT, insertbackground=TEXT)
        self.holes_text.insert("1.0", "0,200\n400,150\n700,300")
        self.holes_text.grid(row=3, column=0, sticky="ew", pady=(0,6))

        tk.Label(body, text="e.g.  0,200  →  start=0, size=200 KB",
                 font=FONT_SMALL, bg=BG, fg=MUTED).grid(row=4, column=0, sticky="w", pady=(0,16))

        tk.Button(body, text="Initialize  →", font=("Segoe UI", 10, "bold"),
                  bg=ACCENT, fg=TEXT_LIGHT, relief="flat", cursor="hand2",
                  padx=18, pady=7, command=self._submit,
                  activebackground="#c9001e", activeforeground=TEXT_LIGHT
                  ).grid(row=5, column=0, sticky="w")

    def _entry(self, parent, var, width=20):
        e = tk.Entry(parent, textvariable=var, font=FONT_MONO, bg=CARD, fg=TEXT,
                     relief="flat", width=width,
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT, insertbackground=TEXT)
        return e

    def _submit(self):
        try:
            total = int(self.total_var.get().strip())
            if total <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Total size must be a positive integer.", parent=self)
            return

        holes = []
        for line in self.holes_text.get("1.0", "end").strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.replace(" ", "").split(",")
            if len(parts) != 2:
                messagebox.showerror("Error", f"Bad hole: '{line}'", parent=self)
                return
            try:
                s, sz = int(parts[0]), int(parts[1])
                if s < 0 or sz <= 0 or s + sz > total:
                    raise ValueError
                holes.append((s, sz))
            except ValueError:
                messagebox.showerror("Error", f"Invalid hole: '{line}'", parent=self)
                return

        self.result = (total, holes)
        self.destroy()


# ─────────────────────────────────────────────
#  PROCESS DIALOG
# ─────────────────────────────────────────────
class ProcessDialog(tk.Toplevel):
    def __init__(self, parent, existing_processes):
        super().__init__(parent)
        self.transient(parent)
        self.title("Add Process")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.result = None
        self.existing = existing_processes
        self._build()
        self.grab_set()
        self.wait_window()

    def _build(self):
        hdr = tk.Frame(self, bg=SIDEBAR, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  Add Process", font=FONT_TITLE,
                 bg=SIDEBAR, fg=TEXT_LIGHT).pack(side="left", padx=16, pady=12)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        tk.Label(body, text="Process name", font=FONT_BODY, bg=BG, fg=MUTED).grid(
            row=0, column=0, sticky="w", pady=(0,4))
        self.name_var = tk.StringVar(value=f"P{len(self.existing)+1}")
        tk.Entry(body, textvariable=self.name_var, font=FONT_MONO, bg=CARD, fg=TEXT,
                 relief="flat", width=14,
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT, insertbackground=TEXT).grid(row=1, column=0, sticky="w", pady=(0,14))

        tk.Label(body, text="Segments  (name, size — one per line)",
                 font=FONT_BODY, bg=BG, fg=MUTED).grid(row=2, column=0, sticky="w", pady=(0,4))
        self.seg_text = tk.Text(body, font=FONT_MONO, bg=CARD, fg=TEXT,
                                relief="flat", width=28, height=5,
                                highlightthickness=1, highlightbackground=BORDER,
                                highlightcolor=ACCENT, insertbackground=TEXT)
        self.seg_text.insert("1.0", "Code,50\nData,200\nStack,100")
        self.seg_text.grid(row=3, column=0, sticky="ew", pady=(0,14))

        tk.Label(body, text="Allocation method", font=FONT_BODY, bg=BG, fg=MUTED).grid(
            row=4, column=0, sticky="w", pady=(0,6))

        self.method_var = tk.StringVar(value="first_fit")
        mf = tk.Frame(body, bg=BG)
        mf.grid(row=5, column=0, sticky="w", pady=(0,16))

        for label, val in [("First-Fit", "first_fit"), ("Best-Fit", "best_fit")]:
            tk.Radiobutton(mf, text=label, variable=self.method_var, value=val,
                           bg=BG, fg=TEXT, selectcolor=CARD,
                           activebackground=BG, font=FONT_BODY).pack(side="left", padx=(0,16))

        tk.Button(body, text="Allocate  →", font=("Segoe UI", 10, "bold"),
                  bg=SUCCESS, fg=TEXT_LIGHT, relief="flat", cursor="hand2",
                  padx=18, pady=7, command=self._submit,
                  activebackground="#20a89e", activeforeground=TEXT_LIGHT
                  ).grid(row=6, column=0, sticky="w")

    def _submit(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Process name cannot be empty.", parent=self)
            return
        if name in self.existing:
            messagebox.showerror("Error", f"Process '{name}' already exists.", parent=self)
            return

        segments = []
        for line in self.seg_text.get("1.0", "end").strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) != 2:
                messagebox.showerror("Error", f"Bad segment: '{line}'", parent=self)
                return
            seg_name = parts[0].strip()
            try:
                sz = int(parts[1].strip())
                if sz <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", f"Invalid size in: '{line}'", parent=self)
                return
            segments.append((seg_name, sz))

        if not segments:
            messagebox.showerror("Error", "At least one segment required.", parent=self)
            return

        self.result = (name, segments, self.method_var.get())
        self.destroy()


# ─────────────────────────────────────────────
#  CHOICE DIALOG
# ─────────────────────────────────────────────
class ChoiceDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt, choices):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.result = None
        self.var = tk.StringVar(value=choices[0])

        hdr = tk.Frame(self, bg=SIDEBAR, height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"  {title}", font=FONT_HEAD, bg=SIDEBAR, fg=TEXT_LIGHT).pack(
            side="left", padx=16, pady=10)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=12)

        tk.Label(body, text=prompt, font=FONT_BODY, bg=BG, fg=MUTED).pack(anchor="w", pady=(0,8))
        for ch in choices:
            tk.Radiobutton(body, text=ch, variable=self.var, value=ch,
                           bg=BG, fg=TEXT, selectcolor=CARD,
                           activebackground=BG, font=FONT_MONO).pack(anchor="w", pady=2)

        tk.Button(body, text="Confirm", font=("Segoe UI", 10, "bold"),
                  bg=DANGER, fg=TEXT_LIGHT, relief="flat", cursor="hand2",
                  padx=16, pady=6, command=self._ok,
                  activebackground="#c9001e").pack(anchor="w", pady=(14,0))

        self.grab_set()
        self.wait_window()

    def _ok(self):
        self.result = self.var.get()
        self.destroy()


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Memory Segmentation Simulator")
        self.configure(bg=BG)
        self.geometry("1160x740")
        self.minsize(960, 620)
        self.mm = None
        self._build_ui()
        self._prompt_setup()

    # ── UI Construction ───────────────────────
    def _build_ui(self):
        self.columnconfigure(0, weight=0)   # sidebar fixed
        self.columnconfigure(1, weight=3)   # canvas
        self.columnconfigure(2, weight=2)   # right panel
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        # ── Sidebar ──────────────────────────
        sidebar = tk.Frame(self, bg=SIDEBAR, width=190)
        sidebar.grid(row=0, column=0, sticky="nsew", rowspan=2)
        sidebar.grid_propagate(False)

        tk.Label(sidebar, text="MEM-SIM", font=("Segoe UI", 15, "bold"),
                 bg=SIDEBAR, fg=TEXT_LIGHT).pack(pady=(24, 4), padx=16, anchor="w")
        tk.Label(sidebar, text="Segmentation v2", font=FONT_SMALL,
                 bg=SIDEBAR, fg=ACCENT2).pack(padx=16, anchor="w")

        tk.Frame(sidebar, bg=ACCENT2, height=1).pack(fill="x", padx=16, pady=20)

        # Sidebar buttons
        self._sidebar_btn(sidebar, "＋  Add Process",  SUCCESS,  self._add_process)
        self._sidebar_btn(sidebar, "✕   Deallocate",   DANGER,   self._deallocate)
        self._sidebar_btn(sidebar, "↺   Reset",        WARNING,  self._reset)

        tk.Frame(sidebar, bg=ACCENT2, height=1).pack(fill="x", padx=16, pady=20)

        # Stats block in sidebar
        self.stat_frame = tk.Frame(sidebar, bg=SIDEBAR)
        self.stat_frame.pack(fill="x", padx=16)
        self._make_stat("Total", "—")
        self._make_stat("Allocated", "—")
        self._make_stat("Free", "—")
        self._make_stat("Processes", "—")
        self._make_stat("Holes", "—")

        # ── Centre: memory canvas ─────────────
        centre = tk.Frame(self, bg=BG)
        centre.grid(row=0, column=1, sticky="nsew", padx=(14, 7), pady=14)
        centre.columnconfigure(0, weight=1)
        centre.rowconfigure(1, weight=1)

        tk.Label(centre, text="MEMORY LAYOUT", font=("Segoe UI", 9, "bold"),
                 bg=BG, fg=MUTED).grid(row=0, column=0, sticky="w", pady=(0, 6))

        canvas_wrap = tk.Frame(centre, bg=CARD,
                               highlightthickness=1, highlightbackground=BORDER)
        canvas_wrap.grid(row=1, column=0, sticky="nsew")
        canvas_wrap.columnconfigure(0, weight=1)
        canvas_wrap.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_wrap, bg=CARD, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda e: self._draw_memory())

        # Legend below canvas
        self.legend_frame = tk.Frame(centre, bg=BG)
        self.legend_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        # ── Right: log + segment tables ───────
        right = tk.Frame(self, bg=BG)
        right.grid(row=0, column=2, sticky="nsew", padx=(7, 14), pady=14)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # Log box
        log_card = tk.Frame(right, bg=CARD,
                            highlightthickness=1, highlightbackground=BORDER)
        log_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        log_card.columnconfigure(0, weight=1)

        tk.Label(log_card, text="  EVENT LOG", font=("Segoe UI", 9, "bold"),
                 bg=CARD2, fg=MUTED, anchor="w").pack(fill="x", ipady=4)

        self.log_box = tk.Text(log_card, font=FONT_MONO_S, bg=CARD, fg=TEXT,
                               relief="flat", height=7, state="disabled",
                               wrap="word", padx=8, pady=6)
        self.log_box.pack(fill="x")
        self.log_box.tag_config("ok",   foreground=SUCCESS)
        self.log_box.tag_config("err",  foreground=DANGER)
        self.log_box.tag_config("info", foreground=ACCENT2)
        self.log_box.tag_config("dim",  foreground=MUTED)

        # Segment tables
        seg_card = tk.Frame(right, bg=CARD,
                            highlightthickness=1, highlightbackground=BORDER)
        seg_card.grid(row=1, column=0, sticky="nsew")
        seg_card.columnconfigure(0, weight=1)
        seg_card.rowconfigure(1, weight=1)

        tk.Label(seg_card, text="  SEGMENT TABLES", font=("Segoe UI", 9, "bold"),
                 bg=CARD2, fg=MUTED, anchor="w").pack(fill="x", ipady=4)

        scroll_wrap = tk.Frame(seg_card, bg=CARD)
        scroll_wrap.pack(fill="both", expand=True)
        scroll_wrap.columnconfigure(0, weight=1)
        scroll_wrap.rowconfigure(0, weight=1)

        self.seg_canvas = tk.Canvas(scroll_wrap, bg=CARD, highlightthickness=0)
        vsb = tk.Scrollbar(scroll_wrap, orient="vertical", command=self.seg_canvas.yview)
        self.seg_canvas.configure(yscrollcommand=vsb.set)
        self.seg_canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self.seg_inner = tk.Frame(self.seg_canvas, bg=CARD)
        self._seg_win = self.seg_canvas.create_window((0, 0), window=self.seg_inner, anchor="nw")
        self.seg_inner.bind("<Configure>",
                            lambda e: self.seg_canvas.configure(
                                scrollregion=self.seg_canvas.bbox("all")))
        self.seg_canvas.bind("<Configure>",
                             lambda e: self.seg_canvas.itemconfig(self._seg_win, width=e.width))

        # ── Status bar ────────────────────────
        self.status_var = tk.StringVar(value="Ready — initialize memory to begin.")
        tk.Label(self, textvariable=self.status_var,
                 font=FONT_SMALL, bg=SIDEBAR, fg=ACCENT2,
                 anchor="w", padx=16).grid(row=1, column=1, columnspan=2, sticky="ew", ipady=5)

    def _sidebar_btn(self, parent, text, color, cmd):
        btn = tk.Button(parent, text=text, font=("Segoe UI", 10, "bold"),
                        bg=color, fg=TEXT_LIGHT, relief="flat", cursor="hand2",
                        command=cmd, anchor="w", padx=16, pady=8,
                        activebackground=color, activeforeground=TEXT_LIGHT,
                        bd=0, highlightthickness=0)
        btn.pack(fill="x", padx=16, pady=3)
        return btn

    def _make_stat(self, label, value):
        row = tk.Frame(self.stat_frame, bg=SIDEBAR)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label, font=FONT_SMALL, bg=SIDEBAR, fg=ACCENT2,
                 width=10, anchor="w").pack(side="left")
        lbl = tk.Label(row, text=value, font=("Consolas", 9, "bold"),
                       bg=SIDEBAR, fg=TEXT_LIGHT, anchor="e")
        lbl.pack(side="right")
        setattr(self, f"_stat_{label.lower()}", lbl)

    def _set_stat(self, label, value):
        getattr(self, f"_stat_{label.lower()}").config(text=str(value))

    # ── Setup / Reset ─────────────────────────
    def _prompt_setup(self):
        dlg = SetupDialog(self)
        if dlg.result is None:
            self.destroy()
            return
        total, holes = dlg.result
        self.mm = MemoryManager(total)
        for s, sz in holes:
            self.mm.add_hole(s, sz)
        self._log(f"Memory initialized: {total} KB total, {len(holes)} hole(s).", "info")
        self._set_stat("Total", f"{total} KB")
        self._refresh()

    def _reset(self):
        self._prompt_setup()

    # ── Actions ───────────────────────────────
    def _add_process(self):
        if not self.mm:
            return
        dlg = ProcessDialog(self, list(self.mm.segment_tables.keys()))
        if dlg.result is None:
            return
        name, segments, method = dlg.result
        ok, msg = self.mm.allocate(name, segments, method)
        self._log(f"[{method.replace('_','-').upper()}]  {msg}", "ok" if ok else "err")
        self._refresh()

    def _deallocate(self):
        if not self.mm or not self.mm.segment_tables:
            messagebox.showinfo("Info", "No processes currently allocated.")
            return
        dlg = ChoiceDialog(self, "Deallocate", "Select process to free:", list(self.mm.segment_tables.keys()))
        if dlg.result is None:
            return
        ok, msg = self.mm.deallocate(dlg.result)
        self._log(msg, "ok" if ok else "err")
        self._refresh()

    # ── Refresh ───────────────────────────────
    def _refresh(self):
        self._draw_memory()
        self._draw_legend()
        self._draw_segment_tables()
        self._update_stats()

    # ── Memory Canvas ─────────────────────────
    def _draw_memory(self):
        if not self.mm:
            return
        c = self.canvas
        c.delete("all")
        W = c.winfo_width()
        H = c.winfo_height()
        if W < 2 or H < 2:
            return

        PAD_L, PAD_R, PAD_T, PAD_B = 58, 14, 14, 14
        bar_w = W - PAD_L - PAD_R
        bar_h = H - PAD_T - PAD_B
        total = self.mm.total_size
        regions = self.mm.memory_map()

        # Background rail
        c.create_rectangle(PAD_L, PAD_T, PAD_L + bar_w, PAD_T + bar_h,
                           fill=CARD2, outline=BORDER, width=1)

        for reg in regions:
            y0 = PAD_T + (reg["start"] / total) * bar_h
            y1 = PAD_T + ((reg["start"] + reg["size"]) / total) * bar_h
            rh = max(y1 - y0, 2)

            if reg["type"] == "hole":
                fill = "#D4EDE9"
                outline = SUCCESS
                label_color = "#1a8a82"
                label = f"FREE  {reg['size']} KB"
            elif reg["type"] == "allocated":
                fill = self._lighten(reg["color"])
                outline = reg["color"]
                label_color = self._darken_text(reg["color"])
                label = f"{reg['process']} · {reg['segment']}  {reg['size']} KB"
            else:
                fill = CARD2
                outline = BORDER
                label_color = MUTED
                label = ""

            c.create_rectangle(PAD_L + 1, y0, PAD_L + bar_w - 1, y0 + rh,
                               fill=fill, outline=outline, width=1)

            # Address label
            c.create_text(PAD_L - 6, y0, text=str(reg["start"]),
                          anchor="e", font=FONT_MONO_S, fill=MUTED)
            c.create_line(PAD_L - 4, y0, PAD_L, y0, fill=BORDER, dash=(2, 2))

            # Segment label inside bar
            if rh > 13 and label:
                c.create_text(PAD_L + 10, y0 + rh / 2, text=label,
                              anchor="w", font=FONT_MONO_S, fill=label_color)

        # End address
        c.create_text(PAD_L - 6, PAD_T + bar_h,
                      text=str(total), anchor="e", font=FONT_MONO_S, fill=MUTED)

    def _lighten(self, hex_color):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = min(255, int(r + (255 - r) * 0.72))
        g = min(255, int(g + (255 - g) * 0.72))
        b = min(255, int(b + (255 - b) * 0.72))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _darken_text(self, hex_color):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r, g, b = int(r * 0.55), int(g * 0.55), int(b * 0.55)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ── Legend ────────────────────────────────
    def _draw_legend(self):
        for w in self.legend_frame.winfo_children():
            w.destroy()
        if not self.mm:
            return

        items = [("Free hole", SUCCESS), ("Uninitialized", BORDER)]
        for proc, color in self.mm.proc_colors.items():
            items.append((proc, color))

        for label, color in items:
            dot = tk.Frame(self.legend_frame, bg=color, width=12, height=12)
            dot.pack(side="left", padx=(0, 4))
            tk.Label(self.legend_frame, text=label, font=FONT_SMALL,
                     bg=BG, fg=MUTED).pack(side="left", padx=(0, 14))

    # ── Segment Tables ────────────────────────
    def _draw_segment_tables(self):
        for w in self.seg_inner.winfo_children():
            w.destroy()

        if not self.mm or not self.mm.segment_tables:
            tk.Label(self.seg_inner, text="No processes allocated yet.",
                     font=FONT_SMALL, bg=CARD, fg=MUTED).pack(anchor="w", padx=10, pady=8)
            return

        for proc, segs in self.mm.segment_tables.items():
            color = self.mm.proc_colors.get(proc, ACCENT)
            light = self._lighten(color)

            card = tk.Frame(self.seg_inner, bg=CARD,
                            highlightthickness=1, highlightbackground=color)
            card.pack(fill="x", padx=6, pady=(0, 8))

            # Process header
            hdr = tk.Frame(card, bg=light)
            hdr.pack(fill="x")
            # Color accent bar
            tk.Frame(hdr, bg=color, width=5).pack(side="left", fill="y")
            tk.Label(hdr, text=f"  {proc}", font=FONT_MONO_B,
                     bg=light, fg=self._darken_text(color)).pack(side="left", pady=5)
            tk.Label(hdr, text=f"{len(segs)} segment(s)  ",
                     font=FONT_SMALL, bg=light, fg=MUTED).pack(side="right", pady=5)

            # Column headers
            col_hdr = tk.Frame(card, bg=CARD2)
            col_hdr.pack(fill="x")
            for txt, w in [("Segment", 9), ("Base", 7), ("Limit", 7), ("End", 7)]:
                tk.Label(col_hdr, text=txt, font=FONT_SMALL, bg=CARD2, fg=MUTED,
                         width=w, anchor="w").pack(side="left", padx=6, pady=2)

            # Rows
            for i, seg in enumerate(segs):
                row_bg = CARD if i % 2 == 0 else "#F9F5F0"
                row = tk.Frame(card, bg=row_bg)
                row.pack(fill="x")
                end = seg["base"] + seg["limit"]
                for val, w in [(seg["segment"], 9), (str(seg["base"]), 7),
                               (str(seg["limit"]), 7), (str(end), 7)]:
                    tk.Label(row, text=val, font=FONT_MONO_S, bg=row_bg, fg=TEXT,
                             width=w, anchor="w").pack(side="left", padx=6, pady=2)

    # ── Stats ─────────────────────────────────
    def _update_stats(self):
        if not self.mm:
            return
        total_alloc = sum(a["size"] for a in self.mm.allocated)
        total_free = sum(h["size"] for h in self.mm.holes)
        self._set_stat("Allocated", f"{total_alloc} KB")
        self._set_stat("Free", f"{total_free} KB")
        self._set_stat("Processes", len(self.mm.segment_tables))
        self._set_stat("Holes", len(self.mm.holes))
        self.status_var.set(
            f"  Allocated: {total_alloc} KB   |   Free: {total_free} KB   |   "
            f"Processes: {len(self.mm.segment_tables)}   |   Holes: {len(self.mm.holes)}"
        )

    # ── Log ───────────────────────────────────
    def _log(self, msg, tag="dim"):
        self.log_box.config(state="normal")
        self.log_box.insert("end", f"›  {msg}\n", tag)
        self.log_box.see("end")
        self.log_box.config(state="disabled")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
