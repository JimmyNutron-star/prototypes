#!/usr/bin/env python3
"""
Quick Python Syntax and Indentation Checker
"""

import os
import ast
import sys
from pathlib import Path

def check_file(filepath):
    """Check a single Python file for indentation and syntax issues"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Check each line
        for i, line in enumerate(lines, 1):
            # Check for tabs
            if '\t' in line:
                leading = line[:len(line) - len(line.lstrip())]
                if '\t' in leading:
                    issues.append(f"Line {i}: Tab character in indentation")
            
            # Check indentation length (should be multiple of 4)
            stripped = line.lstrip()
            indent_len = len(line) - len(stripped)
            if indent_len > 0 and indent_len % 4 != 0:
                issues.append(f"Line {i}: Indentation of {indent_len} spaces (not multiple of 4)")
            
            # Check for mixed tabs/spaces in indentation
            leading = line[:len(line) - len(line.lstrip())]
            if '\t' in leading and ' ' in leading:
                issues.append(f"Line {i}: Mixed tabs and spaces in indentation")
            
            # Check for unbalanced brackets
            if (line.count('(') != line.count(')') or
                line.count('[') != line.count(']') or
                line.count('{') != line.count('}')):
                issues.append(f"Line {i}: Unbalanced brackets/parentheses")
        
        # Try to parse with ast for syntax errors
        content = ''.join(lines)
        ast.parse(content)
        
    except SyntaxError as e:
        issues.append(f"Syntax error: {e}")
    except Exception as e:
        issues.append(f"Error reading file: {e}")
    
    return issues

def main():
    """Main checking function"""
    print("🔍 Python Syntax and Indentation Checker")
    print("=" * 50)
    
    # Get all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip hidden and virtual env directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    if not python_files:
        print("❌ No Python files found!")
        return
    
    print(f"Found {len(python_files)} Python file(s)\n")
    
    total_issues = 0
    files_with_issues = 0
    
    for filepath in python_files:
        issues = check_file(filepath)
        
        if issues:
            files_with_issues += 1
            total_issues += len(issues)
            
            print(f"📄 {filepath}:")
            for issue in issues:
                print(f"   ⚠️  {issue}")
            print()
        else:
            print(f"📄 {filepath}: ✅ OK")
    
    print("=" * 50)
    print(f"Summary:")
    print(f"  Files checked: {len(python_files)}")
    print(f"  Files with issues: {files_with_issues}")
    print(f"  Total issues found: {total_issues}")
    
    if total_issues == 0:
        print("\n✅ All files passed checks!")
    else:
        print("\n❌ Issues found. Please fix before committing.")

if __name__ == "__main__":
    main()