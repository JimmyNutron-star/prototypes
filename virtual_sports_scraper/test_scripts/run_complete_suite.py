import subprocess
import os
import sys
import logging

def run_suite():
    logging.basicConfig(level=logging.INFO)
    logging.info("STARTING COMPLETE TEST SUITE")
    
    # Get all python files in this directory that start with test_
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scripts = [f for f in os.listdir(current_dir) if f.startswith("test_") and f.endswith(".py")]
    
    passed = 0
    total = len(scripts)
    
    for script in scripts:
        logging.info(f"Running {script}...")
        try:
            subprocess.check_call([sys.executable, os.path.join(current_dir, script)])
            logging.info(f"{script}: PASSED")
            passed += 1
        except subprocess.CalledProcessError:
            logging.error(f"{script}: FAILED")
            
    logging.info(f"SUITE COMPLETE. Passed {passed}/{total}")

if __name__ == "__main__":
    run_suite()
