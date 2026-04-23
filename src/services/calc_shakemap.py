import subprocess, os, shlex, logging

logger = logging.getLogger("app.calc_shakemap")

# ShakeMap calculation function
def calc_shakemap(parsed_data):
    event_id = parsed_data["seiscomp_oid"]
    logger.info("Starting ShakeMap calculation for event %s", event_id)
    conda_exe = os.environ.get("CONDA_EXE", "conda")
    conda_env = os.environ.get("SHAKEMAP_CONDA_ENV", "shakemap")

    # წინასწარი შემოწმება: კონფიგურირებულ shell გარემოში ხელმისაწვდომია თუ არა საჭირო ბრძანებები.
    precheck_cmd = (
        f'command -v {shlex.quote(conda_exe)} >/dev/null '
        f'|| (echo "Missing command: {conda_exe}" >&2; exit 127)'
    )
    precheck_result = subprocess.run(
        ["/bin/bash", "-lc", precheck_cmd],
        capture_output=True,
        text=True,
    )
    if precheck_result.returncode != 0:
        raise RuntimeError((precheck_result.stderr or precheck_result.stdout).strip())

    # ShakeMap create command
    sm_create_cmd = (
        f'sm_create -f {event_id} -e ies {parsed_data["time"]} '
        f'{parsed_data["longitude"]} {parsed_data["latitude"]} '
        f'{parsed_data["depth"]} {parsed_data["ml"]} "{parsed_data["desc"]}" -n'
    )
    logger.info("Running ShakeMap for event %s with command: %s", event_id, sm_create_cmd)

    shake_cmd = f'echo {event_id} | shake {event_id} select assemble model contour mapping'

    bash_command = (
        f'eval "$({shlex.quote(conda_exe)} shell.bash hook)" '
        f"&& conda activate {shlex.quote(conda_env)} "
        '&& (command -v sm_create >/dev/null || (echo "Missing command: sm_create" >&2; exit 127)) '
        '&& (command -v shake >/dev/null || (echo "Missing command: shake" >&2; exit 127)) '
        f"&& {sm_create_cmd} && {shake_cmd}"
    )

    result = subprocess.run(
        ["/bin/bash", "-lc", bash_command],
        check=True,
        capture_output=True,
        text=True
    )
    
    logger.info("ShakeMap finished for event %s", event_id)
    # Return stdout and stderr results
    return {
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip()
    }