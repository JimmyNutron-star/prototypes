"""
Create missing __init__.py files
"""

import os

# Create empty __init__.py files
init_files = [
    "scrapers/__init__.py",
    "utils/__init__.py"
]

for file in init_files:
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file), exist_ok=True)
        
        # Create empty file
        with open(file, "w", encoding="utf-8") as f:
            f.write("# Package initialization file\n")
            f.write("__version__ = '1.0.0'\n")
        
        print(f"✅ Created: {file}")
        
    except Exception as e:
        print(f"❌ Error creating {file}: {e}")

print("\n🎉 All __init__.py files created!")