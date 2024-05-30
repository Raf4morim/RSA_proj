import subprocess
import threading

def run_script(script_name):
    subprocess.run(["python3", script_name])

# List of scripts to run
scripts = ["ambulance.py", "front_car.py", "violating_car.py", "front_car2.py"]

# Create a thread for each script
threads = []
for script in scripts:
    thread = threading.Thread(target=run_script, args=(script,))
    threads.append(thread)

# Start all threads
for thread in threads:
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()

print("All scripts have completed.")