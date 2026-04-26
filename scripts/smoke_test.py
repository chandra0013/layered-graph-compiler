import subprocess
import sys

def run_cmd(cmd: list[str]) -> None:
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing {' '.join(cmd)}")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    print("Success.\n")

def main():
    print("Running LGC Smoke Test...\n")
    
    run_cmd(["lgc", "build", "."])
    run_cmd(["lgc", "query", ".", "how does query routing work", "--format", "json"])
    run_cmd(["lgc", "run-benchmark", "."])
    run_cmd(["lgc", "export-benchmark", "."])
    run_cmd(["lgc", "visualize", "."])
    
    print("All smoke tests passed!")

if __name__ == "__main__":
    main()
