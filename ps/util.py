import subprocess

from .logging import print_error

def run_process_in_dir(cwd, args):
    args = args.strip()
    try:
        process = subprocess.run(args.split(" "), text=True, check=True, cwd=cwd)
    except:
        print_error("Failed to run: " + args)
        return False
    return True

def run_process_in_dir_and_return_stdout(cwd, args):
    args = args.strip()
    try:
        process = subprocess.run(args.split(" "), stdout=subprocess.PIPE, text=True, check=True, cwd=cwd)
    except:
        print_error("Failed to run: " + args)
        return None
    return process.stdout

def depth_indent(depth):
    return "  "*depth;
