import subprocess, os, shlex, logging

def calc_shakemap(parsed_data):
    event_id = parsed_data["event_id"]

    sm_create_cmd = (
        f'sm_create -f {event_id} -e ies {parsed_data["time"]} '
        f'{parsed_data["longitude"]} {parsed_data["latitude"]} '
        f'{parsed_data["depth_km"]} {parsed_data["magnitude"]} " " -n'
    )

    shake_cmd = f'echo {event_id} | shake {event_id} select assemble model contour mapping'

    conda_exe = os.environ.get("CONDA_EXE", "conda")

    bash_command = f'eval "$({shlex.quote(conda_exe)} shell.bash hook)" && conda activate shakemap && {sm_create_cmd} && {shake_cmd}'

    subprocess.run(["/bin/bash", "-lc", bash_command], check=True)
    
    logging.info(f"ShakeMap finished for event {event_id}")