import tkinter as tk
from tkinter import ttk, scrolledtext
import json


class LockErrorDialog:
    def __init__(self, parent, lock_error_data, on_retry, on_force_cleanup, on_safe_cleanup):
        self.parent = parent
        self.data = lock_error_data or {}
        self.on_retry = on_retry
        self.on_force_cleanup = on_force_cleanup
        self.on_safe_cleanup = on_safe_cleanup

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("⚠ Problem z aktualizacją")
        self.dialog.geometry("600x380")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_ui()

    def setup_ui(self):
        header = ttk.Frame(self.dialog, padding=10)
        header.pack(fill='x')
        ttk.Label(header, text="⚠ Aktualizacja już w toku", font=("Arial", 14, "bold")).pack()

        info = ttk.LabelFrame(self.dialog, text="Szczegóły", padding=10)
        info.pack(fill='both', expand=True, padx=10, pady=10)

        pid = self.data.get('pid', 'Nieznany')
        age = int(self.data.get('age_seconds', 0))
        alive = self.data.get('process_alive', False)

        if age < 60:
            time_str = f"{age} sekund"
        elif age < 3600:
            time_str = f"{int(age/60)} minut"
        else:
            time_str = f"{int(age/3600)} godzin"

        info_text = f"PID procesu: {pid}\nCzas od rozpoczęcia: {time_str}\nStatus procesu: {'DZIAŁA' if alive else 'ZAKOŃCZONY'}"
        ttk.Label(info, text=info_text, justify='left').pack(anchor='w')

        if alive:
            warning = "⚠ Uwaga: Proces nadal działa. Wymuszone zamknięcie może spowodować utratę utraty danych."
            ttk.Label(info, text=warning, foreground='orange', wraplength=560).pack(pady=6, anchor='w')

        # Buttons
        btns = ttk.Frame(self.dialog)
        btns.pack(pady=8)

        if alive:
            ttk.Button(btns, text="🔄 Spróbuj ponownie za 30s", command=self.retry_later).pack(side='left', padx=6)
            ttk.Button(btns, text="🗑️ Wymuś czyszczenie i kontynuuj", command=self.force_cleanup).pack(side='left', padx=6)
        else:
            ttk.Button(btns, text="🧹 Wyczyść i kontynuuj", command=self.safe_cleanup).pack(side='left', padx=6)

        ttk.Button(btns, text="✖ Anuluj", command=self.cancel).pack(side='left', padx=6)

        # Diagnostic details
        details = self.data.get('details') or self.data.get('lock_data') or self.data
        try:
            ds = json.dumps(details, indent=2)
        except Exception:
            ds = str(details)

        log_frame = ttk.LabelFrame(self.dialog, text="Logi diagnostyczne", padding=6)
        log_frame.pack(fill='both', padx=10, pady=(0,10))
        txt = scrolledtext.ScrolledText(log_frame, height=6, wrap='word')
        txt.pack(fill='both')
        txt.insert('1.0', ds)
        txt.config(state='disabled')

    def retry_later(self):
        self.dialog.destroy()
        if callable(self.on_retry):
            self.on_retry()

    def force_cleanup(self):
        self.dialog.destroy()
        if callable(self.on_force_cleanup):
            self.on_force_cleanup()

    def safe_cleanup(self):
        self.dialog.destroy()
        if callable(self.on_safe_cleanup):
            self.on_safe_cleanup()

    def cancel(self):
        self.dialog.destroy()
