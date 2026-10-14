#!/usr/bin/env python3
"""
Temporary Unknown Custom Agent CLI for Agy Studio Conformance Testing.
Not part of the 8 known CLIs. Proves universal runtime capability.
"""
import sys
import time
from pathlib import Path

def main():
    args = sys.argv[1:]
    
    if not args or "--version" in args or "-v" in args:
        print("UnknownAgent CLI v3.1.0 (Standalone Python Agent)")
        sys.exit(0)

    # Parse prompt from -p or --prompt
    prompt = ""
    for i, a in enumerate(args):
        if a in ["-p", "--prompt"] and i + 1 < len(args):
            prompt = args[i + 1]
            break
        elif not a.startswith("-"):
            prompt = a
            break

    if not prompt:
        print("No prompt provided")
        sys.exit(1)

    if "Respond with exactly AGY_AGENT_TEST_OK" in prompt:
        print("AGY_AGENT_TEST_OK")
        sys.exit(0)

    if "sleep" in prompt.lower() or "hang" in prompt.lower():
        # Sleep to allow testing process cancellation
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            pass
        sys.exit(0)

    if "artifact" in prompt.lower() or "write" in prompt.lower() or "fibonacci" in prompt.lower():
        # Create an artifact in cwd
        out_file = Path("custom_output.txt")
        out_file.write_text("Hello from Unknown Custom Agent CLI!\nGenerated artifact successfully.\n", encoding="utf-8")
        print(f"Artifact created: {out_file.name}")
        sys.exit(0)

    print(f"Executed prompt: {prompt}")
    sys.exit(0)

if __name__ == "__main__":
    main()
