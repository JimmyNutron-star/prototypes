"""
Data saving and file management
"""

import json
import pandas as pd
import os
from datetime import datetime
from config import DATA_DIR, SAVE_AS_JSON, SAVE_AS_CSV, SAVE_AS_EXCEL

class FileHandler:
    def __init__(self, data_type):
        """Initialize file handler for specific data type"""
        self.data_type = data_type  # 'matchday', 'results', 'standings'
        self.output_dir = os.path.join(DATA_DIR, data_type)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_filename(self, prefix="", extension="json"):
        """Generate timestamped filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if prefix:
            filename = f"{prefix}_{timestamp}.{extension}"
        else:
            filename = f"{self.data_type}_{timestamp}.{extension}"
        return os.path.join(self.output_dir, filename)
    
    def save_json(self, data, filename=None):
        """Save data as JSON"""
        if not SAVE_AS_JSON:
            return None
        
        if not filename:
            filename = self.generate_filename(extension="json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def save_csv(self, data, filename=None):
        """Save data as CSV"""
        if not SAVE_AS_CSV or not data:
            return None
        
        if not filename:
            filename = self.generate_filename(extension="csv")
        
        # Convert to DataFrame if it's a list
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame([data])
        
        df.to_csv(filename, index=False, encoding='utf-8')
        return filename
    
    def save_excel(self, data, filename=None):
        """Save data as Excel"""
        if not SAVE_AS_EXCEL or not data:
            return None
        
        if not filename:
            filename = self.generate_filename(extension="xlsx")
        
        # Convert to DataFrame if it's a list
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame([data])
        
        df.to_excel(filename, index=False)
        return filename
    
    def save_all_formats(self, data, prefix=""):
        """Save data in all configured formats"""
        saved_files = {}
        
        if SAVE_AS_JSON:
            saved_files['json'] = self.save_json(data, self.generate_filename(prefix, "json"))
        
        if SAVE_AS_CSV:
            saved_files['csv'] = self.save_csv(data, self.generate_filename(prefix, "csv"))
        
        if SAVE_AS_EXCEL:
            saved_files['excel'] = self.save_excel(data, self.generate_filename(prefix, "xlsx"))
        
        return saved_files
    
    def load_latest_file(self, extension="json"):
        """Load the most recent file of specified type"""
        try:
            files = [f for f in os.listdir(self.output_dir) if f.endswith(f".{extension}")]
            if not files:
                return None
            
            latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(self.output_dir, x)))
            filepath = os.path.join(self.output_dir, latest_file)
            
            if extension == "json":
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif extension == "csv":
                return pd.read_csv(filepath)
            elif extension == "xlsx":
                return pd.read_excel(filepath)
            
        except Exception as e:
            print(f"Error loading file: {e}")
            return None