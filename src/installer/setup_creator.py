import PyInstaller.__main__
import os

def create_setup():
    print("Starting build process...")
    
    # Define build arguments
    # Note: Paths separator handling for cross-platform safety, though this is Windows specific task.
    
    # We need to include data files: src, locales, resources
    add_data = [
        'src;src',
        'locales;locales',
        'resources;resources',
        'config.ini;.',
        'version.json;.'
    ]
    
    args = [
        'money_mods.py',
        '--name=SupermarketMoneyBooster',
        '--onefile',
        '--windowed',
        '--icon=icons/app.ico',
        '--clean',
        '--noconfirm'
    ]
    
    for d in add_data:
        args.append(f'--add-data={d}')
        
    try:
        PyInstaller.__main__.run(args)
        print("Build complete. executable is in dist/ folder.")
    except Exception as e:
        print(f"Build failed: {e}")

if __name__ == "__main__":
    create_setup()
