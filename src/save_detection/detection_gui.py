import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from datetime import datetime
import os

class SaveDetectionGUI:
    def __init__(self, parent_frame, scanner, manager, on_save_selected=None):
        self.parent = parent_frame
        self.scanner = scanner
        self.manager = manager
        self.on_save_selected = on_save_selected
        
        self.setup_ui()
        self.scanning = False
    
    def setup_ui(self):
        detection_frame = ttk.LabelFrame(self.parent, text="Save Detection", padding="10")
        detection_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scan Buttons
        button_frame = ttk.Frame(detection_frame)
        button_frame.pack(fill="x", pady=5)
        
        ttk.Button(button_frame, text="🔍 Full Scan", 
                  command=self.start_system_scan).pack(side="left", padx=5)
        
        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(detection_frame, 
                                           variable=self.progress_var,
                                           maximum=100)
        self.progress_bar.pack(fill="x", pady=10)
        
        self.status_label = ttk.Label(detection_frame, text="Ready to scan...")
        self.status_label.pack()
        
        # Save List
        list_frame = ttk.Frame(detection_frame)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("Status", "Name", "Path", "Modified", "Money")
        self.save_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.save_tree.heading(col, text=col)
            self.save_tree.column(col, width=100 if col != "Path" else 250)
            
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", 
                                 command=self.save_tree.yview)
        self.save_tree.configure(yscrollcommand=scrollbar.set)
        
        self.save_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind double-click
        self.save_tree.bind("<Double-1>", lambda e: self.modify_selected())
        
        # Actions
        action_frame = ttk.Frame(detection_frame)
        action_frame.pack(fill="x", pady=5)
        
        ttk.Button(action_frame, text="💾 Use and Modify Selected", 
                  command=self.modify_selected).pack(side="left", padx=2)
        
        ttk.Button(action_frame, text="Info", 
                  command=self.show_info).pack(side="left", padx=2)
        
    def start_system_scan(self):
        if not self.scanning:
            self.scanning = True
            thread = threading.Thread(target=self._system_scan_thread)
            thread.daemon = True
            thread.start()
    
    def _system_scan_thread(self):
        self.update_status("Scanning system...", 10)
        
        try:
            self.update_status("Detecting game installation...", 30)
            # Find and classify implicitly runs detection
            all_saves = self.manager.find_and_classify_all_saves()
            self.update_status("Finalizing results...", 90)
            
            self.parent.after(0, self._display_results, all_saves)
            
            count = len(all_saves['slots']) + (1 if all_saves['primary'] else 0)
            self.update_status(f"Found {count} saves", 100)
            
            if count == 0:
                 self.parent.after(0, lambda: messagebox.showwarning("Scan Complete", "No saves found. Check if game is installed or try manual selection."))
            
        except Exception as e:
            import traceback
            error_msg = f"Scan Error: {str(e)}\n{traceback.format_exc()}"
            self.update_status("Scan Failed", 0)
            self.parent.after(0, lambda: messagebox.showerror("Error", error_msg))
            print(error_msg)
        finally:
            self.scanning = False
            
    def update_status(self, text, progress):
        self.parent.after(0, lambda: self.status_label.config(text=text))
        self.parent.after(0, lambda: self.progress_var.set(progress))
    
    def _display_results(self, all_saves):
        # Clear
        for item in self.save_tree.get_children():
            self.save_tree.delete(item)
        
        if all_saves['primary']:
            self._add_save_to_tree(all_saves['primary'], "⭐ Primary")
        
        for save in all_saves['slots']:
            if save != all_saves['primary']:
                self._add_save_to_tree(save, "📁 Slot")
                
        for backup in all_saves['backups'][:10]: # Show more backups
            self._add_save_to_tree(backup, "💾 Backup")
            
    def _add_save_to_tree(self, save_info, status):
        money = save_info.get('money_amount')
        money_str = f"{money:,.2f}$" if money is not None else "Unknown"
        
        modified = save_info.get('modified', datetime.now())
        modified_str = modified.strftime("%Y-%m-%d %H:%M")
        
        self.save_tree.insert("", "end", values=(
            status,
            save_info['filename'],
            save_info['path'],
            modified_str,
            money_str
        ))
        
    def modify_selected(self):
        selected = self.save_tree.selection()
        if not selected:
            return
        
        # Get path from item
        item = self.save_tree.item(selected[0])
        path = item['values'][2]
        
        if self.on_save_selected:
            self.on_save_selected(path)
        else:
            messagebox.showinfo("Selection", f"Selected for modification: {path}")
        # In full integration, we would pass this back to main app
        
    def show_info(self):
        selected = self.save_tree.selection()
        if selected:
            item = self.save_tree.item(selected[0])
            messagebox.showinfo("Info", str(item['values']))
