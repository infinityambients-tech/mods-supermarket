"""
Supermarket Money Booster - Legacy Edition
Extremely powerful modification tool for Supermarket Simulator.

IMPLEMENTED FEATURES:
- [x] Money Modification (Add/Set)
- [x] Store Level Modification
- [x] Experience Points (XP) Editor
- [x] Store Upgrade Points (Expansion Points)
- [x] One-Click License Unlocker (All products)
- [x] Infinite Customer Satisfaction (Store Rating)
- [x] Staff Stat Booster (Max Speed & Accuracy)
- [x] Advanced Save Detection System
- [x] Automatic Backup System
- [X] Staff Stat Booster (Speed & Accuracy)
- [X] Infinite Customer Satisfaction
- [X] instant Restocking System
- [X] Dynamic Pricing Automator

FUTURE SUGGESTIONS & PLANNED:

"Nzawa" Suggestions Memory:
- Remember to check AppData/LocalLow/NoktaGames for save files.
- StoreLevel and StoreExperiencePoints are the core growth keys.
- UnlockedLicenses is the list of product IDs.
"""

from src.gui.main_window import MoneyBoosterGUI

def run_application():
    """Initializes and runs the Money Booster GUI."""
    print("Launching Supermarket Money Booster...")
    app = MoneyBoosterGUI()
    app.run()

if __name__ == "__main__":
    run_application()
