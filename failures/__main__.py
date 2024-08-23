import os
import sys
from pathlib import Path

import django

if __name__ == "__main__":
    ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent
    sys.path.append(str(ROOT_DIR / "failures"))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    django.setup()

    from failures.commands import main

    main()
