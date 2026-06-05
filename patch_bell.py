import sys
import re

def patch_protected_layout():
    with open('backend/../frontend/src/components/layout/ProtectedLayout.tsx', 'r', encoding='utf-8') as f:
        content = f.read()

    # Import
    if 'import NotificationDropdown' not in content:
        content = content.replace(
            'import { useWebSocket } from "../../hooks/useWebSocket"',
            'import { useWebSocket } from "../../hooks/useWebSocket"\nimport NotificationDropdown from "../NotificationDropdown"'
        )
    
    # Replace bell wrapper div
    # The structure is: <div className="relative" ref={notifRef}> ... </div> 
    # Let's find it.
    start_str = '            {/* Notifications */}'
    end_str = '            {/* User Dropdown */}'
    
    if start_str in content and end_str in content:
        start_idx = content.find(start_str)
        end_idx = content.find(end_str)
        
        if start_idx != -1 and end_idx != -1:
            replacement = '            {/* Notifications */}\n            <NotificationDropdown />\n\n'
            content = content[:start_idx] + replacement + content[end_idx:]
    
    with open('backend/../frontend/src/components/layout/ProtectedLayout.tsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched ProtectedLayout")

def patch_apoteker_layout():
    with open('backend/../frontend/src/components/layout/ApotekerLayout.tsx', 'r', encoding='utf-8') as f:
        content = f.read()

    # Import
    if 'import NotificationDropdown' not in content:
        content = content.replace(
            'import { useWebSocket } from "../../hooks/useWebSocket"',
            'import { useWebSocket } from "../../hooks/useWebSocket"\nimport NotificationDropdown from "../NotificationDropdown"'
        )
    
    # Replace bell wrapper
    start_str = '            {/* Notification Bell */}'
    end_str = '          </div>\n        </header>'
    
    if start_str in content and end_str in content:
        start_idx = content.find(start_str)
        end_idx = content.find(end_str)
        
        if start_idx != -1 and end_idx != -1:
            replacement = '            {/* Notification Bell */}\n            <div className="flex items-center">\n              <NotificationDropdown />\n            </div>\n'
            content = content[:start_idx] + replacement + content[end_idx:]

    with open('backend/../frontend/src/components/layout/ApotekerLayout.tsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched ApotekerLayout")

patch_protected_layout()
patch_apoteker_layout()
