import subprocess
import sys
import logging

def run_suite():
    logging.basicConfig(level=logging.INFO)
    logging.info("STARTING MARKET TEST SUITE")
    
    scripts = [
        "test_market_selected.py",
        "test_all_markets.py",
        "test_market_switching.py",
        "test_odds_market.py"
    ]
    
    for script in scripts:
        logging.info(f"Running {script}...")
        try:
            subprocess.check_call([sys.executable, script])
            logging.info(f"{script}: PASSED")
        except subprocess.CalledProcessError:
            logging.error(f"{script}: FAILED")

if __name__ == "__main__":
    run_suite()
