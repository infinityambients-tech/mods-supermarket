import tkinter as tk
from tkinter import ttk, messagebox
from src.save_editor.advanced_stats_modifier import AdvancedStatsModifier
from src.save_editor.error_diagnostic import ErrorDiagnosticSystem
from pathlib import Path

class FixedStatsGUI:
    def __init__(self, parent, get_save_path_cb):
        self.parent = parent
        self.get_save_path = get_save_path_cb
        self.modifier = AdvancedStatsModifier()
        self.diagnostic = ErrorDiagnosticSystem()
        self.setup_ui()

    def setup_ui(self):
        stats_frame = ttk.LabelFrame(self.parent, text="Statystyki Sklepu", padding=10)
        stats_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Level
        level_frame = ttk.Frame(stats_frame)
        level_frame.pack(fill='x', pady=5)
        ttk.Label(level_frame, text="Poziom sklepu:", width=15).pack(side='left')
        self.level_var = tk.StringVar(value="")
        ttk.Entry(level_frame, textvariable=self.level_var, width=10).pack(side='left', padx=5)
        ttk.Button(level_frame, text="Ustaw poziom", command=lambda: self.modify_stat('level', self.level_var.get())).pack(side='left', padx=5)
        ttk.Button(level_frame, text="MAX POZIOM", command=lambda: self.modify_stat('level', '99')).pack(side='left', padx=5)

        # XP
        xp_frame = ttk.Frame(stats_frame)
        xp_frame.pack(fill='x', pady=5)
        ttk.Label(xp_frame, text="Punkty XP:", width=15).pack(side='left')
        self.xp_var = tk.StringVar(value="")
        ttk.Entry(xp_frame, textvariable=self.xp_var, width=10).pack(side='left', padx=5)
        ttk.Button(xp_frame, text="Ustaw XP", command=lambda: self.modify_stat('xp', self.xp_var.get())).pack(side='left', padx=5)

        # Upgrade points
        points_frame = ttk.Frame(stats_frame)
        points_frame.pack(fill='x', pady=5)
        ttk.Label(points_frame, text="Punkty ulepszeń:", width=15).pack(side='left')
        self.points_var = tk.StringVar(value="")
        ttk.Entry(points_frame, textvariable=self.points_var, width=10).pack(side='left', padx=5)
        ttk.Button(points_frame, text="Ustaw punkty", command=lambda: self.modify_stat('upgrade_points', self.points_var.get())).pack(side='left', padx=5)

        # Rating
        rating_frame = ttk.Frame(stats_frame)
        rating_frame.pack(fill='x', pady=5)
        ttk.Label(rating_frame, text="Ocena sklepu:", width=15).pack(side='left')
        self.rating_var = tk.StringVar(value="")
        ttk.Entry(rating_frame, textvariable=self.rating_var, width=10).pack(side='left', padx=5)
        ttk.Button(rating_frame, text="Ustaw ocenę", command=lambda: self.modify_stat('rating', self.rating_var.get())).pack(side='left', padx=5)

        # Diagnostics
        ttk.Button(stats_frame, text="🔧 Diagnostyka błędów", command=self.run_diagnostics).pack(pady=10)

    def modify_stat(self, stat_type: str, value_str: str):
        # validate
        try:
            if value_str is None or value_str == '':
                messagebox.showerror('Błąd', 'Podaj wartość')
                return
            val = float(value_str) if '.' in value_str else int(value_str)
        except ValueError:
            messagebox.showerror('Błąd', f'Nieprawidłowa wartość: {value_str}')
            return

        save_path = self.get_save_path()
        if not save_path:
            messagebox.showerror('Błąd', 'Nie wybrano pliku save')
            return

        res = self.modifier.modify_statistic(save_path, stat_type, val)
        if res.get('success'):
            msg = f"Pomyślnie zmieniono {stat_type} na {val}"
            if res.get('field_path'):
                msg += f"\nŚcieżka: {res.get('field_path')}"
            messagebox.showinfo('Sukces', msg)
        else:
            # show diagnostics
            self.show_detailed_error(res, stat_type, val)

    def show_detailed_error(self, result, stat_type, value):
        # reuse diagnostic system to produce deeper report
        save_path = self.get_save_path()
        diagnosis = self.diagnostic.diagnose_modification_error(save_path, stat_type, value)
        # present simple dialog with issues
        issues = '\n'.join(diagnosis.get('issues', [])) or 'Brak szczegółów'
        details = f"Problemy:\n{issues}\n\nPlik info:\n{diagnosis.get('file_info')}\n\nStruktura:\n{diagnosis.get('structure_analysis')}"
        messagebox.showerror('Błąd modyfikacji', f"{result.get('message')}\n\n{details}")

    def run_diagnostics(self):
        save_path = self.get_save_path()
        if not save_path:
            messagebox.showerror('Błąd', 'Nie wybrano pliku save')
            return
        diag = self.diagnostic.diagnose_modification_error(save_path, 'level', 0)
        msg = 'Issues:\n' + '\n'.join(diag.get('issues', [])) if diag.get('issues') else 'No issues detected'
        messagebox.showinfo('Diagnostyka', msg)
