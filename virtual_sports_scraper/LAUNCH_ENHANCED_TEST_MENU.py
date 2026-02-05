import os
import sys
import subprocess
import logging

def main():
    # Setup simple logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    print("="*60)
    print("   VIRTUAL SPORTS SCRAPER - LAUNCHER")
    print("="*60)
    print("Initializing environment...")

    # Ensure dependencies are installed (lightweight check)
    try:
        import selenium
        import tkinter
        print("Dependencies seem to be present.")
    except ImportError:
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Launch GUI
    print("Launching GUI...")
    gui_script = "test_menu_gui_enhanced.py"
    
    if os.path.exists(gui_script):
        subprocess.call([sys.executable, gui_script])
    else:
        print(f"ERROR: Could not find {gui_script}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
