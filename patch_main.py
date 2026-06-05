import sys

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'from app.api.v1 import notification_routes' not in content:
    content = content.replace(
        'from app.api.v1 import (\n    auth_routes,\n    user_routes,\n    product_routes,\n    order_routes,\n    dashboard_routes,\n    audit_routes,\n    apoteker_routes\n)',
        'from app.api.v1 import (\n    auth_routes,\n    user_routes,\n    product_routes,\n    order_routes,\n    dashboard_routes,\n    audit_routes,\n    apoteker_routes,\n    notification_routes\n)'
    )
    
    # Just in case the format is different
    if 'notification_routes' not in content:
        content = content.replace(
            'import (\n    auth_routes,\n    user_routes,\n    product_routes,\n    order_routes,\n    dashboard_routes,\n    audit_routes,\n    apoteker_routes,\n)',
            'import (\n    auth_routes,\n    user_routes,\n    product_routes,\n    order_routes,\n    dashboard_routes,\n    audit_routes,\n    apoteker_routes,\n    notification_routes,\n)'
        )

    content = content.replace(
        'app.include_router(apoteker_routes.router, prefix="/api/v1")',
        'app.include_router(apoteker_routes.router, prefix="/api/v1")\napp.include_router(notification_routes.router, prefix="/api/v1")'
    )

    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Registered notification_routes in main.py")
else:
    print("Already registered")
