import subprocess, os, shlex, logging

# ShakeMap calculation function
def calc_shakemap(parsed_data):
    event_id = parsed_data["event_id"]
    logging.info(f"Starting ShakeMap calculation for event {event_id}")
    # ShakeMap create command
    sm_create_cmd = (
        f'sm_create -f {event_id} -e ies {parsed_data["time"]} '
        f'{parsed_data["longitude"]} {parsed_data["latitude"]} '
        f'{parsed_data["depth"]} {parsed_data["ml"]} "{parsed_data["desc"]}" -n'
    )
    logging.info(f"Running ShakeMap for event {event_id} with command: {sm_create_cmd}")

    shake_cmd = f'echo {event_id} | shake {event_id} select assemble model contour mapping'

    conda_exe = os.environ.get("CONDA_EXE", "conda")

    bash_command = f'eval "$({shlex.quote(conda_exe)} shell.bash hook)" && conda activate shakemap && {sm_create_cmd} && {shake_cmd}'

    result = subprocess.run(
        ["/bin/bash", "-lc", bash_command],
        check=True,
        capture_output=True,
        text=True
    )
    
    logging.info(f"ShakeMap finished for event {event_id}")
    # Return stdout and stderr results
    return {
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip()
    }