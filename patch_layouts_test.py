import sys
import re

def patch_layout(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add import
    if 'import NotificationDropdown' not in content:
        content = content.replace(
            'import { useWebSocket } from "../../hooks/useWebSocket"',
            'import { useWebSocket } from "../../hooks/useWebSocket"\nimport NotificationDropdown from "../NotificationDropdown"'
        )
        content = content.replace(
            'import { useWebSocket } from "../../hooks/useWebSocket";',
            'import { useWebSocket } from "../../hooks/useWebSocket";\nimport NotificationDropdown from "../NotificationDropdown";'
        )

    # 2. Replace bell section with <NotificationDropdown />
    # For ApotekerLayout
    if '{/* Notification Bell */}' in content:
        # Regex to find the Notification Bell div and replace it
        # Since it's multiline and complex, we can just find the boundaries.
        start = content.find('{/* Notification Bell */}')
        # We need to find where the <div className="relative"> ends. It's tricky with regex.
        # Let's just do a manual string replacement for the known blocks, or use a simpler approach.
        pass

    return content

# Instead of complex regex, let's just write a robust python script to do it.
