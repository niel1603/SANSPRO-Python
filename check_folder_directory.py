import subprocess

# Path to handle.exe
handle_path = r"D:\COMPUTATIONAL\Python\SANSPRO\data\Handle\handle.exe"

# The process executable
process_exe = r"Sanspro530-Student.exe"

# Run handle.exe for the specific process
result = subprocess.run(
    [handle_path, "-accepteula", "-p", process_exe],
    capture_output=True,
    text=True
)

# Filter lines containing "Example"
for line in result.stdout.splitlines():
    if "Example" in line:
        print(line)
