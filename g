#!/usr/bin/env python3
import os
import re

BASE_DIR = os.getcwd()
BASE_HTML = os.path.join(BASE_DIR, "templates", "desktop", "base.html")

def patch_base():
    if not os.path.exists(BASE_HTML):
        print(f"❌ {BASE_HTML} not found.")
        return

    with open(BASE_HTML, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if extra_head block already exists
    if '{% block extra_head %}' in content:
        print("✅ extra_head block already present.")
        return

    # Insert before </head>
    if '</head>' in content:
        new_content = content.replace('</head>', '    {% block extra_head %}{% endblock %}\n</head>')
        with open(BASE_HTML, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Added {% block extra_head %} to desktop/base.html")
    else:
        print("❌ Could not find </head> tag.")

if __name__ == "__main__":
    patch_base()
