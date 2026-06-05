import sys
import re

with open('backend/app/services/order_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import
if 'from app.services.notification_service import notifier' not in content:
    content = content.replace(
        'from app.utils.audit import log_audit',
        'from app.utils.audit import log_audit\nfrom app.services.notification_service import notifier'
    )

# 2. Checkout
checkout_notif = """
        if requires_rx:
            await notifier.notify_role("apoteker", "Resep Baru", f"Pesanan {order.order_code} menunggu verifikasi resep.", type="order", link=f"/apoteker/verifikasi/{order.id}")
        elif order.order_type == OrderType.ONLINE:
            await notifier.notify_user(current_user.id, "Pesanan Berhasil", f"Silakan lakukan pembayaran untuk pesanan {order.order_code}.", type="order", link="/orders")

        # Low stock check
        for ded in deductions:
            if ded["stock_remaining"] <= ded["min_stock"]:
                warn_msg = f"Stok produk {ded['product_name']} menipis (sisa {ded['stock_remaining']})."
                await notifier.notify_role("admin", "Peringatan Stok Menipis", warn_msg, level="warning", type="stock", link="/admin/products")
                await notifier.notify_role("apoteker", "Peringatan Stok Menipis", warn_msg, level="warning", type="stock", link="/apoteker/produk")
                await notifier.notify_role("kasir", "Peringatan Stok Menipis", warn_msg, level="warning", type="stock", link="/pos")

        return OrderOut.from_orm_model(
"""
if 'await notifier.notify_role("apoteker", "Resep Baru"' not in content:
    content = content.replace('        return OrderOut.from_orm_model(', checkout_notif, 1)

# 3. upload_payment_proof
if 'await notifier.notify_role("kasir", "Pembayaran Baru"' not in content:
    content = content.replace(
        '        order = await self.repo.update_status(order, OrderStatus.MENUNGGU_KONFIRMASI_KASIR)\n\n        await log_audit(',
        '        order = await self.repo.update_status(order, OrderStatus.MENUNGGU_KONFIRMASI_KASIR)\n\n        await notifier.notify_role("kasir", "Pembayaran Baru", f"Bukti transfer untuk {order.order_code} telah diunggah.", type="order", link="/pos/orders")\n\n        await log_audit('
    )

# 4. kasir_confirm_payment
if 'await notifier.notify_role("apoteker", "Pesanan Lunas"' not in content:
    content = content.replace(
        '        order = await self.repo.update_status(order, OrderStatus.DIPROSES)\n        \n        await log_audit(',
        '        order = await self.repo.update_status(order, OrderStatus.DIPROSES)\n        \n        await notifier.notify_role("apoteker", "Pesanan Lunas", f"Pesanan {order.order_code} lunas dan siap dikemas.", type="order", link="/apoteker/orders")\n        await notifier.notify_user(order.user_id, "Pembayaran Dikonfirmasi", f"Pembayaran {order.order_code} berhasil. Pesanan diproses.", type="order", link="/orders")\n\n        await log_audit('
    )

# 5. kasir_reject_payment
if 'await notifier.notify_user(order.user_id, "Pembayaran Ditolak"' not in content:
    content = content.replace(
        '        order = await self.repo.update_payment_proof(order, None)\n        \n        await log_audit(',
        '        order = await self.repo.update_payment_proof(order, None)\n        \n        await notifier.notify_user(order.user_id, "Pembayaran Ditolak", f"Bukti transfer pesanan {order.order_code} ditolak: {reason}", level="error", type="order", link="/orders")\n\n        await log_audit('
    )

# 6. apoteker_ship_order
if 'await notifier.notify_user(order.user_id, "Pesanan Dikirim"' not in content:
    content = content.replace(
        '        if tracking_number:\n            order = await self.repo.update_tracking(order, tracking_number)\n            \n        await log_audit(',
        '        if tracking_number:\n            order = await self.repo.update_tracking(order, tracking_number)\n            \n        await notifier.notify_user(order.user_id, "Pesanan Dikirim", f"Pesanan {order.order_code} sedang dalam perjalanan.", type="order", link="/orders")\n\n        await log_audit('
    )

# 7. confirm_received
if 'await notifier.notify_user(order.user_id, "Pesanan Selesai"' not in content:
    content = content.replace(
        '        order = await self.repo.update_status(order, OrderStatus.SELESAI)\n        \n        await log_audit(',
        '        order = await self.repo.update_status(order, OrderStatus.SELESAI)\n        \n        await notifier.notify_user(order.user_id, "Pesanan Selesai", f"Pesanan {order.order_code} telah selesai.", type="order", link="/orders")\n\n        await log_audit('
    )

# 8. review_prescription
review_approved = """                await self.repo.update_status(order, new_order_status)
                await self.repo.update_payment_deadline(order, payment_deadline)
                await notifier.notify_user(order.user_id, "Resep Disetujui", f"Resep pesanan {order.order_code} disetujui. Silakan lakukan pembayaran.", type="order", link="/orders")"""

review_rejected = """                new_order_status = OrderStatus.DIBATALKAN
                await self.repo.update_status(order, new_order_status)
                await notifier.notify_user(order.user_id, "Resep Ditolak", f"Resep pesanan {order.order_code} ditolak. Pesanan dibatalkan.", level="error", type="order", link="/orders")"""

if 'Resep Disetujui' not in content:
    content = content.replace(
        '                await self.repo.update_status(order, new_order_status)\n                await self.repo.update_payment_deadline(order, payment_deadline)',
        review_approved
    )
    content = content.replace(
        '                new_order_status = OrderStatus.DIBATALKAN\n                await self.repo.update_status(order, new_order_status)',
        review_rejected
    )

with open('backend/app/services/order_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("order_service.py patched successfully")
