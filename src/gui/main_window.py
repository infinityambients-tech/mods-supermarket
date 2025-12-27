import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import configparser
from pathlib import Path

from src.gui.themes import Theme
from src.gui.language import Language
from src.save_editor.save_manager import SaveManager
from src.save_editor.json_editor import SaveEditor
from src.save_editor.backup_system import BackupSystem

# New Detection Modules
from src.save_detection.save_scanner import SupermarketSaveScanner
from src.save_detection.save_manager import MultiSaveManager
from src.save_detection.detection_gui import SaveDetectionGUI

# Update System
from src.updater.github_updater import GitHubUpdater
from src.updater.version_check import VersionCheck

class MoneyBoosterGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("600x500") # Expanded for tabs
        
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        
        self.current_lang = self.config.get('Settings', 'language', fallback='pl')
        self.current_theme_name = self.config.get('Settings', 'theme', fallback='dark')
        
        self.language = Language(self.current_lang)
        self.theme = Theme.get_theme(self.current_theme_name)
        
        # Legacy components
        self.save_manager = SaveManager()
        self.save_editor = SaveEditor()
        self.backup_system = BackupSystem()
        
        # New Detection components
        self.scanner = SupermarketSaveScanner()
        self.multi_save_manager = MultiSaveManager(self.scanner)
        
        self.current_save_path = None
        
        self.apply_theme()
        self.setup_ui()
        self.load_initial_data()
        
        # Initialize Updater (Real repository)
        self.local_version = VersionCheck.get_local_version()
        self.updater = GitHubUpdater("infinityambients-tech", "mods-supermarket", self.local_version)
        
        # Check for updates after UI loads
        self.root.after(2000, self.check_for_updates)

    def apply_theme(self):
        theme = self.theme
        self.root.configure(bg=theme['bg'])
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background=theme['bg'])
        style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])
        style.configure('TButton', background=theme['button_bg'], foreground=theme['button_fg'])
        style.map('TButton', background=[('active', theme['highlight'])])
        style.configure('TEntry', fieldbackground=theme['entry_bg'], foreground=theme['entry_fg'])
        style.configure('TNotebook', background=theme['bg'])
        style.configure('TNotebook.Tab', background=theme['button_bg'], foreground=theme['button_fg'])
        style.map('TNotebook.Tab', background=[('selected', theme['highlight'])])

    def setup_ui(self):
        self.root.title(self.language.get("app_title"))
        
        # Notebook for Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Quick Mod (Legacy GUI)
        self.quick_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.quick_tab, text="Quick Mod")
        self._setup_quick_tab(self.quick_tab)
        
        # Tab 2: Advanced Detection
        self.detection_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.detection_tab, text="Advanced Detection")
        self.detection_gui = SaveDetectionGUI(
            self.detection_tab, 
            self.scanner, 
            self.multi_save_manager,
            on_save_selected=self.handle_detection_selection
        )
        
        # Settings Bar (Common)
        settings_frame = ttk.Frame(self.root)
        settings_frame.pack(side="bottom", fill="x", pady=5, padx=5)
        ttk.Button(settings_frame, text="PL/EN", command=self.toggle_lang).pack(side="right", padx=2)
        ttk.Button(settings_frame, text="Dark/Light", command=self.toggle_theme).pack(side="right", padx=2)
        
        # Menu
        self.create_menu()

    def handle_detection_selection(self, file_path):
        """Callback for when a save is selected in the detection tab"""
        self.current_save_path = Path(file_path)
        self.update_info()
        # Switch to Quick Mod tab
        self.notebook.select(self.quick_tab)
        messagebox.showinfo(self.language.get("success_title"), f"Switched to: {self.current_save_path.name}")

    def _setup_quick_tab(self, parent):
        # Frame
        main_frame = ttk.Frame(parent, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Status
        self.status_label = ttk.Label(main_frame, text=self.language.get("status_no_save"))
        self.status_label.pack(pady=(0, 10))
        
        # Stats Display Frame
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="x", pady=5)
        
        self.money_label = ttk.Label(stats_frame, text=self.language.get("current_money").format("0"))
        self.money_label.pack(pady=2)
        
        self.level_label = ttk.Label(stats_frame, text=self.language.get("current_level").format("0"))
        self.level_label.pack(pady=2)
        
        self.xp_label = ttk.Label(stats_frame, text=self.language.get("current_xp").format("0"))
        self.xp_label.pack(pady=2)
        
        self.points_label = ttk.Label(stats_frame, text=self.language.get("current_points").format("0"))
        self.points_label.pack(pady=2)
        
        self.rating_label = ttk.Label(stats_frame, text=self.language.get("current_rating").format("0"))
        self.rating_label.pack(pady=2)
        
        # Input Controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=15, fill="x")
        
        # Money Row
        money_row = ttk.Frame(control_frame)
        money_row.pack(fill="x", pady=2)
        ttk.Label(money_row, text=self.language.get("amount_label"), width=15).pack(side="left")
        self.money_entry = ttk.Entry(money_row, width=15)
        self.money_entry.pack(side="left", padx=5)
        self.add_btn = ttk.Button(money_row, text=self.language.get("add_button"), command=self.add_money)
        self.add_btn.pack(side="left", padx=2)
        self.max_btn = ttk.Button(money_row, text=self.language.get("max_button"), command=self.set_max_money)
        self.max_btn.pack(side="left", padx=2)
        
        # Level Row
        level_row = ttk.Frame(control_frame)
        level_row.pack(fill="x", pady=2)
        ttk.Label(level_row, text=self.language.get("current_level").split(":")[0] + ":", width=15).pack(side="left")
        self.level_entry = ttk.Entry(level_row, width=15)
        self.level_entry.pack(side="left", padx=5)
        self.set_level_btn = ttk.Button(level_row, text=self.language.get("set_level_button"), command=self.set_level)
        self.set_level_btn.pack(side="left", padx=2)
        self.max_level_btn = ttk.Button(level_row, text=self.language.get("max_level_button"), command=self.set_max_level)
        self.max_level_btn.pack(side="left", padx=2)
        
        # XP Row
        xp_row = ttk.Frame(control_frame)
        xp_row.pack(fill="x", pady=2)
        ttk.Label(xp_row, text=self.language.get("current_xp").split(":")[0] + ":", width=15).pack(side="left")
        self.xp_entry = ttk.Entry(xp_row, width=15)
        self.xp_entry.pack(side="left", padx=5)
        self.set_xp_btn = ttk.Button(xp_row, text=self.language.get("set_xp_button"), command=self.set_xp)
        self.set_xp_btn.pack(side="left", padx=2)

        # Points Row
        points_row = ttk.Frame(control_frame)
        points_row.pack(fill="x", pady=2)
        ttk.Label(points_row, text=self.language.get("current_points").split(":")[0] + ":", width=15).pack(side="left")
        self.points_entry = ttk.Entry(points_row, width=15)
        self.points_entry.pack(side="left", padx=5)
        self.set_points_btn = ttk.Button(points_row, text=self.language.get("set_points_button"), command=self.set_points)
        self.set_points_btn.pack(side="left", padx=2)

        # Rating Row
        rating_row = ttk.Frame(control_frame)
        rating_row.pack(fill="x", pady=2)
        ttk.Label(rating_row, text=self.language.get("current_rating").split(":")[0] + ":", width=15).pack(side="left")
        self.rating_entry = ttk.Entry(rating_row, width=15)
        self.rating_entry.pack(side="left", padx=5)
        self.set_rating_btn = ttk.Button(rating_row, text=self.language.get("set_rating_button"), command=self.set_rating)
        self.set_rating_btn.pack(side="left", padx=2)

        # Utility Buttons Row
        util_row = ttk.Frame(control_frame)
        util_row.pack(fill="x", pady=10)
        
        self.unlock_btn = ttk.Button(util_row, text=self.language.get("unlock_licenses_button"), command=self.unlock_licenses)
        self.unlock_btn.pack(side="left", fill="x", expand=True, padx=2)
        
        self.boost_staff_btn = ttk.Button(util_row, text=self.language.get("boost_staff_button"), command=self.boost_staff)
        self.boost_staff_btn.pack(side="left", fill="x", expand=True, padx=2)
        
        self.repair_btn = ttk.Button(util_row, text=self.language.get("repair_interaction_btn"), command=self.repair_interaction)
        self.repair_btn.pack(side="left", fill="x", expand=True, padx=2)
        
        self.backup_btn = ttk.Button(main_frame, text=self.language.get("backup_button"), command=self.create_backup)
        self.backup_btn.pack(pady=10)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.language.get("menu_file"), menu=file_menu)
        file_menu.add_command(label=self.language.get("menu_select_save"), command=self.manual_select_save)
        file_menu.add_separator()
        file_menu.add_command(label=self.language.get("menu_exit"), command=self.root.quit)

    def load_initial_data(self):
        found_file = self.save_manager.find_save_file()
        if found_file:
            self.current_save_path = found_file
            self.update_info()

    def update_info(self):
        if self.current_save_path:
            self.status_label.config(text=self.language.get("status_save_found") + f": {self.current_save_path.name}")
            stats = self.save_editor.get_current_stats(self.current_save_path)
            self.money_label.config(text=self.language.get("current_money").format(f"{stats['money']:,.2f}"))
            self.level_label.config(text=self.language.get("current_level").format(int(stats['level'] or 0)))
            self.xp_label.config(text=self.language.get("current_xp").format(int(stats['xp'] or 0)))
            self.points_label.config(text=self.language.get("current_points").format(int(stats['points'] or 0)))
            self.rating_label.config(text=self.language.get("current_rating").format(f"{stats['rating'] or 0:.1f}"))
        else:
            self.status_label.config(text=self.language.get("status_no_save"))

    def add_money(self):
        if not self.current_save_path:
            messagebox.showerror(self.language.get("error_title"), "No save file selected.")
            return
        try:
            amount = float(self.money_entry.get())
            if self.save_editor.modify_money(self.current_save_path, amount, 'add'):
                messagebox.showinfo(self.language.get("success_title"), self.language.get("success_add").format(amount))
                self.update_info()
            else:
                messagebox.showerror(self.language.get("error_title"), "Failed to modify save.")
        except ValueError:
            messagebox.showerror(self.language.get("error_title"), self.language.get("error_amount"))

    def set_level(self):
        if not self.current_save_path:
            messagebox.showerror(self.language.get("error_title"), "No save file selected.")
            return
        try:
            level = int(self.level_entry.get())
            if self.save_editor.modify_level(self.current_save_path, level):
                messagebox.showinfo(self.language.get("success_title"), self.language.get("success_level").format(level))
                self.update_info()
            else:
                messagebox.showerror(self.language.get("error_title"), "Failed to modify level.")
        except ValueError:
            messagebox.showerror(self.language.get("error_title"), "Enter valid level integer!")

    def set_xp(self):
        if not self.current_save_path:
            messagebox.showerror(self.language.get("error_title"), "No save file selected.")
            return
        try:
            xp = int(self.xp_entry.get())
            if self.save_editor.modify_xp(self.current_save_path, xp):
                messagebox.showinfo(self.language.get("success_title"), self.language.get("success_xp").format(xp))
                self.update_info()
            else:
                messagebox.showerror(self.language.get("error_title"), "Failed to modify XP.")
        except ValueError:
            messagebox.showerror(self.language.get("error_title"), "Enter valid XP integer!")

    def set_points(self):
        if not self.current_save_path:
            messagebox.showerror(self.language.get("error_title"), "No save file selected.")
            return
        try:
            points = int(self.points_entry.get())
            if self.save_editor.modify_store_points(self.current_save_path, points):
                messagebox.showinfo(self.language.get("success_title"), self.language.get("success_points").format(points))
                self.update_info()
            else:
                messagebox.showerror(self.language.get("error_title"), "Failed to modify points.")
        except ValueError:
            messagebox.showerror(self.language.get("error_title"), "Enter valid points integer!")

    def set_rating(self):
        if not self.current_save_path:
            messagebox.showerror(self.language.get("error_title"), "No save file selected.")
            return
        try:
            rating = float(self.rating_entry.get())
            if self.save_editor.modify_rating(self.current_save_path, rating):
                messagebox.showinfo(self.language.get("success_title"), self.language.get("success_rating").format(rating))
                self.update_info()
            else:
                messagebox.showerror(self.language.get("error_title"), "Failed to modify rating.")
        except ValueError:
            messagebox.showerror(self.language.get("error_title"), "Enter valid rating number!")

    def boost_staff(self):
        if not self.current_save_path:
            messagebox.showerror(self.language.get("error_title"), "No save file selected.")
            return
        if self.save_editor.boost_staff_stats(self.current_save_path):
            messagebox.showinfo(self.language.get("success_title"), self.language.get("success_staff"))
            self.update_info()
        else:
            messagebox.showerror(self.language.get("error_title"), "Failed to boost staff stats. Make sure you have hired employees!")

    def repair_interaction(self):
        if not self.current_save_path:
            messagebox.showerror(self.language.get("error_title"), "No save file selected.")
            return
        if self.save_editor.repair_interaction(self.current_save_path):
            messagebox.showinfo(self.language.get("success_title"), self.language.get("success_repair"))
            self.update_info()
        else:
            messagebox.showerror(self.language.get("error_title"), "Failed to repair interaction.")

    def unlock_licenses(self):
        if not self.current_save_path:
            messagebox.showerror(self.language.get("error_title"), "No save file selected.")
            return
        if self.save_editor.unlock_all_licenses(self.current_save_path):
            messagebox.showinfo(self.language.get("success_title"), self.language.get("success_licenses"))
            self.update_info()
        else:
            messagebox.showerror(self.language.get("error_title"), "Failed to unlock licenses.")

    def set_max_money(self):
        self.money_entry.delete(0, tk.END)
        self.money_entry.insert(0, "9999999")
        self.add_money()

    def set_max_level(self):
        self.level_entry.delete(0, tk.END)
        self.level_entry.insert(0, "99")
        self.set_level()

    def create_backup(self):
        if self.current_save_path:
            path = self.backup_system.create_backup(self.current_save_path)
            if path:
                messagebox.showinfo("Backup", f"Backup created at: {path.name}")

    def manual_select_save(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if filename:
            self.current_save_path = Path(filename)
            self.update_info()
            
    def toggle_theme(self):
        new_theme = 'light' if self.current_theme_name == 'dark' else 'dark'
        self.current_theme_name = new_theme
        self.theme = Theme.get_theme(new_theme)
        self.apply_theme()
        
    def toggle_lang(self):
        new_lang = 'en' if self.current_lang == 'pl' else 'pl'
        self.current_lang = new_lang
        self.language.load_locale(new_lang)
        self.root.title(self.language.get("app_title"))
        self.status_label.config(text=self.language.get("status_no_save") if not self.current_save_path else self.language.get("status_save_found"))
        self.update_info()
        self.add_btn.config(text=self.language.get("add_button"))
        self.max_btn.config(text=self.language.get("max_button"))
        self.set_level_btn.config(text=self.language.get("set_level_button"))
        self.max_level_btn.config(text=self.language.get("max_level_button"))
        self.set_xp_btn.config(text=self.language.get("set_xp_button"))
        self.set_points_btn.config(text=self.language.get("set_points_button"))
        self.set_rating_btn.config(text=self.language.get("set_rating_button"))
        self.boost_staff_btn.config(text=self.language.get("boost_staff_button"))
        self.repair_btn.config(text=self.language.get("repair_interaction_btn"))
        self.unlock_btn.config(text=self.language.get("unlock_licenses_button"))
        self.backup_btn.config(text=self.language.get("backup_button"))
        self.create_menu()

    def check_for_updates(self):
        """Checks for new version on GitHub."""
        update_info = self.updater.check_for_updates()
        if update_info.get('available'):
            latest_v = update_info['version']
            msg = self.language.get("update_desc").format(latest_v)
            if messagebox.askyesno(self.language.get("update_available"), msg):
                self.perform_update(update_info['download_url'])

    def perform_update(self, download_url):
        """Handles the download and application of the update."""
        progress_popup = tk.Toplevel(self.root)
        progress_popup.title(self.language.get("updating"))
        progress_popup.geometry("300x100")
        ttk.Label(progress_popup, text=self.language.get("updating")).pack(pady=20)
        self.root.update()

        if self.updater.download_update(download_url):
            if self.updater.apply_update():
                messagebox.showinfo(self.language.get("success_title"), self.language.get("update_ready"))
                self.root.quit()
        else:
            messagebox.showerror(self.language.get("error_title"), "Update failed to download.")
            progress_popup.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MoneyBoosterGUI()
    app.run()
