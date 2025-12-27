"""
Supermarket Money Booster - Legacy Edition
Extremely powerful modification tool for Supermarket Simulator.

IMPLEMENTED FEATURES:
- [x] Money Modification (Add/Set)
- [x] Store Level Modification
- [x] Experience Points (XP) Editor
- [x] Store Upgrade Points (Expansion Points)
- [x] One-Click License Unlocker (All products)
- [x] Advanced Save Detection System
- [x] Automatic Backup System

FUTURE SUGGESTIONS & PLANNED:
- [ ] Staff Stat Booster (Speed & Accuracy)
- [ ] Infinite Customer Satisfaction
- [ ] instant Restocking System
- [ ] Dynamic Pricing Automator

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
