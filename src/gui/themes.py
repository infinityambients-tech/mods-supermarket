class Theme:
    DARK = {
        "bg": "#2e2e2e",
        "fg": "#ffffff",
        "button_bg": "#4a4a4a",
        "button_fg": "#ffffff",
        "entry_bg": "#3e3e3e",
        "entry_fg": "#ffffff",
        "highlight": "#007acc"
    }
    
    LIGHT = {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "button_bg": "#e0e0e0",
        "button_fg": "#000000",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "highlight": "#007acc"
    }

    @staticmethod
    def get_theme(name):
        return Theme.DARK if name == 'dark' else Theme.LIGHT
