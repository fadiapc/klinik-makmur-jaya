import sys

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
if 'from app.services.expiry_service import expiry_check_loop' not in content:
    content = content.replace(
        'from app.core.database import close_db, init_db',
        'from app.core.database import close_db, init_db\nfrom app.services.expiry_service import expiry_check_loop\nimport asyncio'
    )

# Add task
if 'expiry_task = asyncio.create_task(expiry_check_loop())' not in content:
    content = content.replace(
        '    await init_db()\n\n    yield',
        '    await init_db()\n    \n    expiry_task = asyncio.create_task(expiry_check_loop())\n\n    yield'
    )
    content = content.replace(
        '    yield  # 🚦 application runs here\n\n    # Shutdown: release resources\n    await close_db()',
        '    yield  # 🚦 application runs here\n\n    # Shutdown: release resources\n    expiry_task.cancel()\n    await close_db()'
    )

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched main.py to include expiry_check_loop")
