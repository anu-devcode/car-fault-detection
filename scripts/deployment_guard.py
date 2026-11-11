"""Block hosting builds until the owner explicitly opens the production stage."""

import os
import sys


def main():
    if os.environ.get("CAR_HUB_ALLOW_DEPLOY") == "true":
        return 0
    print("Deployment disabled during development. See docs/roadmap.md.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
