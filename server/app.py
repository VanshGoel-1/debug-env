# Required by `openenv validate` / `openenv push`.
# All logic lives in debug_env/server/app.py.
from debug_env.server.app import app  # noqa: F401
from debug_env.server.app import main as _main


def main():
    _main()


if __name__ == "__main__":
    main()
