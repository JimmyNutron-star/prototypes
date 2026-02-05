import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import subprocess
import os
import sys
import time
from datetime import datetime
from config.settings import LEAGUES, MARKETS
from config.paths import TEST_RESULTS_DIR, SCREENSHOTS_DIR

class TestMenuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Sports Scraper - Enhanced Test Menu")
        self.root.geometry("1100x750")
        
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        self.colors = {
            'bg': '#f0f0f0',
            'header': '#333333',
            'startup': '#27ae60', # Green
            'league': '#2980b9',  # Blue
            'market': '#8e44ad',  # Purple
            'odds': '#d35400',    # Orange
            'live': '#e74c3c',    # Red
            'data': '#7f8c8d'     # Grey
        }
        
    def create_widgets(self):
        # Sidebar for controls
        control_frame = ttk.Frame(self.root, width=300, padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Title
        ttk.Label(control_frame, text="CONFIGURATION", font=("Helvetica", 12, "bold")).pack(pady=10)
        
        # League Selection
        ttk.Label(control_frame, text="Select League:").pack(anchor=tk.W)
        self.league_var = tk.StringVar(value=LEAGUES[0])
        self.league_combo = ttk.Combobox(control_frame, textvariable=self.league_var, values=LEAGUES + ["All Leagues"], state="readonly")
        self.league_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Market Selection
        ttk.Label(control_frame, text="Select Market:").pack(anchor=tk.W)
        self.market_var = tk.StringVar(value=MARKETS[0])
        self.market_combo = ttk.Combobox(control_frame, textvariable=self.market_var, values=MARKETS + ["All Markets"], state="readonly")
        self.market_combo.pack(fill=tk.X, pady=(0, 20))
        
        # Separator
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Test Categories
        self.create_test_buttons(control_frame)
        
        # Main Output Area
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="TEST OUTPUT LOG", font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
        
        self.log_area = scrolledtext.ScrolledText(main_frame, state='disabled', height=30)
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_area.tag_config('INFO', foreground='black')
        self.log_area.tag_config('ERROR', foreground='red')
        self.log_area.tag_config('SUCCESS', foreground='green')
        self.log_area.tag_config('HEADER', foreground='blue', font=("Helvetica", 10, "bold"))
        
        # Bottom controls from main frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Open Results Folder", command=self.open_results_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Run Complete Suite", command=self.run_complete_suite).pack(side=tk.RIGHT, padx=5)
        
    def create_test_button(self, parent, text, cmd, color_key):
        btn = tk.Button(parent, text=text, command=cmd, bg=self.colors[color_key], fg="white", font=("Arial", 9, "bold"), relief=tk.FLAT, pady=5)
        btn.pack(fill=tk.X, pady=2)
        return btn

    def create_test_buttons(self, parent):
        # Group: Startup
        ttk.Label(parent, text="STARTUP TESTS", font=("Arial", 8, "bold")).pack(anchor=tk.W, pady=(5,0))
        self.create_test_button(parent, "Test Popup Handler", lambda: self.run_script("test_popup.py"), 'startup')
        self.create_test_button(parent, "Test Browser Setup", lambda: self.run_script("test_browser.py"), 'startup')
        self.create_test_button(parent, "Test Navigation", lambda: self.run_script("test_navigation.py"), 'startup')
        
        # Group: League
        ttk.Label(parent, text="LEAGUE TESTS", font=("Arial", 8, "bold")).pack(anchor=tk.W, pady=(10,0))
        self.create_test_button(parent, "Test Selected League", self.run_selected_league_test, 'league')
        self.create_test_button(parent, "Test All Leagues", lambda: self.run_script("test_all_leagues.py"), 'league')
        self.create_test_button(parent, "Test League Switching", lambda: self.run_script("test_league_switching.py"), 'league')

        # Group: Market
        ttk.Label(parent, text="MARKET TESTS", font=("Arial", 8, "bold")).pack(anchor=tk.W, pady=(10,0))
        self.create_test_button(parent, "Test Selected Market", self.run_selected_market_test, 'market')
        self.create_test_button(parent, "Test All Markets", lambda: self.run_script("test_all_markets.py"), 'market')
        
        # Group: Odds
        ttk.Label(parent, text="ODDS TESTS", font=("Arial", 8, "bold")).pack(anchor=tk.W, pady=(10,0))
        self.create_test_button(parent, "Scrape Odds (League)", self.run_odds_league_test, 'odds')
        self.create_test_button(parent, "Scrape Odds (Market)", self.run_odds_market_test, 'odds')
        
        # Group: Live/Data
        ttk.Label(parent, text="LIVE & DATA TESTS", font=("Arial", 8, "bold")).pack(anchor=tk.W, pady=(10,0))
        self.create_test_button(parent, "Test Timer Watcher", lambda: self.run_script("test_timer.py"), 'live')
        self.create_test_button(parent, "Test Data Storage", lambda: self.run_script("test_storage.py"), 'data')

    def log(self, message, level='INFO'):
        self.log_area.configure(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] ", 'INFO')
        self.log_area.insert(tk.END, f"{message}\n", level)
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def clear_log(self):
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state='disabled')

    def open_results_folder(self):
        try:
            os.startfile(TEST_RESULTS_DIR)
        except Exception as e:
            self.log(f"Failed to open folder: {e}", 'ERROR')

    def run_script(self, script_name, args=[]):
        threading.Thread(target=self._execute_script, args=(script_name, args), daemon=True).start()

    def _execute_script(self, script_name, args):
        self.log(f"--- STARTING {script_name} ---", 'HEADER')
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_scripts", script_name)
        
        cmd = [sys.executable, script_path] + args
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # Real-time output reading
            for line in process.stdout:
                self.log(line.strip())
            
            process.wait()
            
            if process.returncode == 0:
                self.log(f"--- {script_name} SUCCEEDED ---", 'SUCCESS')
            else:
                self.log(f"--- {script_name} FAILED ---", 'ERROR')
                # Read stderr if fail
                err = process.stderr.read()
                if err:
                    self.log(f"ERROR DETAILS: {err}", 'ERROR')
                    
        except Exception as e:
            self.log(f"Execution Error: {e}", 'ERROR')

    # Specific Runners
    def run_selected_league_test(self):
        league = self.league_var.get()
        self.run_script("test_league_selected.py", ["--league", league])

    def run_selected_market_test(self):
        market = self.market_var.get()
        self.run_script("test_market_selected.py", ["--market", market])

    def run_odds_league_test(self):
        league = self.league_var.get()
        self.run_script("test_odds_league.py", ["--league", league])
        
    def run_odds_market_test(self):
        market = self.market_var.get()
        self.run_script("test_odds_market.py", ["--market", market])
        
    def run_complete_suite(self):
        self.run_script("run_complete_suite.py")

if __name__ == "__main__":
    root = tk.Tk()
    app = TestMenuGUI(root)
    root.mainloop()
