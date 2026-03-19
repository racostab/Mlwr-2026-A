import argparse
import os
import subprocess
import sys


def run_terminal_command():
    parser = argparse.ArgumentParser(
        description="A simple wrapper to execute terminal commands."
    )

    parser.add_argument("command", help="The main terminal command to run.", default='ls')
    parser.add_argument("params", nargs=argparse.REMAINDER, help="Additional parameters for the command.", default='-la')

    args = parser.parse_args()

    full_cmd = [args.command] + args.params

    try:
        #result = subprocess.run(
        #    full_cmd,
        #    capture_output=True,
        #    text=True,
        #    check=True
        #)
        #sys.stdout.write("--- Command Output ---\n")
        #sys.stdout.write(result.stdout)

        stream = os.popen(' '.join(full_cmd))
        output = stream.read()
        sys.stdout.write("--- Command Output ---\n")
        sys.stdout.write(output)

    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error: Command failed with return code {e.returncode}\n")
        sys.stderr.write(f"Details: {e.stderr}\n")

    except FileNotFoundError:
        sys.stderr.write(f"Error: The command '{args.command}' was not found.\n")

if __name__ == "__main__":
    run_terminal_command()
