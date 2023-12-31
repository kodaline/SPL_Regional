import subprocess
import os
import sys  # import sys for sys.executable
os.environ["OMP_NUM_THREADS"] = "1"


def get_script_directory():
    # If the 'SCRIPT_DIR' environment variable is set, use it
    script_dir = os.environ.get('SCRIPT_DIR')
    
    if script_dir:
        return script_dir
    
    # Otherwise, try to find out whether running in GitHub Codespace
    elif '/workspaces/' in os.getcwd():
        return '/workspaces/SPL_Regional/Python/'
    
    # If not in GitHub Codespace, assume running locally
    else:
        # Assume the scripts are in the same directory as this script
        return os.path.dirname(os.path.abspath(__file__))

def run_scripts():
    script_directory = get_script_directory()
    
    # Change to directory where scripts are located
    os.chdir(script_directory)
    
    scripts_to_run = [
        "1_SPL_Processor_v0.4.py",
        "2_Points_Summary_v.0.5.py",
        "3_Graph_Generator_v.0.2.py",
        "4_Player_Ranking_Gen_v0.2.py",
        "5_Player_Clusters_v.0.4.py",
        "6_Fanta_Team_gen_v.0.1.py",
        "7_Fanta_Table_v.0.1.py"
    ]
    
    for script in scripts_to_run:
        print(f"Executing {script}...")
        subprocess.run([sys.executable, script])  # Use sys.executable instead of 'python3'
        print(f"{script} completed.")

if __name__ == "__main__":
    run_scripts()
