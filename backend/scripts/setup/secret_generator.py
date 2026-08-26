import re
import secrets
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def write_secret_to_env(key: str, value: str, env_path: Path) -> None:
    """Create or update `key=value` in `env_path`, preserving every other line."""
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    pattern = re.compile(rf"^{re.escape(key)}=")

    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n")


def main() -> None:
    jwt_secret = secrets.token_urlsafe(32)
    write_secret_to_env("JWT_SECRET", jwt_secret, ENV_PATH)
    print(f"JWT_SECRET generated and written to {ENV_PATH}")


if __name__ == "__main__":
    main()
