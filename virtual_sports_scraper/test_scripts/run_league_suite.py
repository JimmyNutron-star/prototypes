import subprocess
import sys
import logging

def run_suite():
    logging.basicConfig(level=logging.INFO)
    logging.info("STARTING LEAGUE TEST SUITE")
    
    scripts = [
        "test_league_selected.py",
        "test_all_leagues.py",
        "test_league_switching.py",
        "test_odds_league.py"
    ]
    
    for script in scripts:
        logging.info(f"Running {script}...")
        try:
            # We use python executable to run the sub-script
            subprocess.check_call([sys.executable, script])
            logging.info(f"{script}: PASSED")
        except subprocess.CalledProcessError:
            logging.error(f"{script}: FAILED")
            # Continue running others? Or stop? Prompt implies independent testing, so continue.

if __name__ == "__main__":
    run_suite()
