"""Print the OPENAI_API_KEY value from the project's ignored .env.local (empty if absent)."""

from pathlib import Path

path = Path("/Users/atsushi/Desktop/projects/personal/pals/.env.local")
value = ""
for line in path.read_text(encoding="utf-8").splitlines():
    if line.startswith("OPENAI_API_KEY="):
        value = line.split("=", 1)[1].strip().strip("'\"")
print(value, end="")
