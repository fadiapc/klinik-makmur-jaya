import sys

new_methods = '''
    async def kasir_confirm_payment(
        self,
        order_id: int,
        current_user: User,
        request: Request,
    ) -> OrderOut:
        """
        Kasir mengkonfirmasi bahwa bukti transfer valid dan dana sudah masuk.
        """
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status != OrderStatus.MENUNGGU_KONFIRMASI_KASIR:
            raise HTTPException(status_code=400, detail="Order is not waiting for kasir confirmation")

        requires_rx_flag = any(item.product.requires_prescription for item in order.items)
        order = await self.repo.update_status(order, OrderStatus.DIPROSES)
        
        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="KASIR_CONFIRM_PAYMENT",
            module="ORDER",
            target_type="Order",
            target_id=order.id,
            new_value={"status": OrderStatus.DIPROSES.value},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return OrderOut.from_orm_model(
            order=order,
            requires_prescription=requires_rx_flag,
            prescription_required_and_missing=requires_rx_flag and (not order.prescription or order.prescription.status != PrescriptionStatus.APPROVED),
            stock_deductions=[]
        )

    async def kasir_reject_payment(
        self,
        order_id: int,
        reason: str,
        current_user: User,
        request: Request,
    ) -> OrderOut:
        """
        Kasir menolak bukti transfer (misal: buram, palsu, kurang).
        """
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status != OrderStatus.MENUNGGU_KONFIRMASI_KASIR:
            raise HTTPException(status_code=400, detail="Order is not waiting for kasir confirmation")

        requires_rx_flag = any(item.product.requires_prescription for item in order.items)
        # Kembali ke MENUNGGU_PEMBAYARAN, dan hapus URL proof
        order = await self.repo.update_status(order, OrderStatus.MENUNGGU_PEMBAYARAN)
        order = await self.repo.update_payment_proof(order, None)
        
        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="KASIR_REJECT_PAYMENT",
            module="ORDER",
            target_type="Order",
            target_id=order.id,
            new_value={"status": OrderStatus.MENUNGGU_PEMBAYARAN.value, "reason": reason},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return OrderOut.from_orm_model(
            order=order,
            requires_prescription=requires_rx_flag,
            prescription_required_and_missing=requires_rx_flag and (not order.prescription or order.prescription.status != PrescriptionStatus.APPROVED),
            stock_deductions=[]
        )

    async def apoteker_ship_order(
        self,
        order_id: int,
        tracking_number: str,
        current_user: User,
        request: Request,
    ) -> OrderOut:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status != OrderStatus.DIPROSES:
            raise HTTPException(status_code=400, detail="Order is not in DIPROSES status")

        requires_rx_flag = any(item.product.requires_prescription for item in order.items)
        order = await self.repo.update_status(order, OrderStatus.DIKIRIM)
        if tracking_number:
            order = await self.repo.update_tracking(order, tracking_number)
            
        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="SHIP_ORDER",
            module="ORDER",
            target_type="Order",
            target_id=order.id,
            new_value={"status": OrderStatus.DIKIRIM.value, "tracking_number": tracking_number},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return OrderOut.from_orm_model(
            order=order,
            requires_prescription=requires_rx_flag,
            prescription_required_and_missing=requires_rx_flag and (not order.prescription or order.prescription.status != PrescriptionStatus.APPROVED),
            stock_deductions=[]
        )

    async def confirm_received(
        self,
        order_id: int,
        current_user: User,
        request: Request,
    ) -> OrderOut:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
            
        if order.user_id != current_user.id and current_user.role.name not in ["admin", "kasir"]:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        if order.status != OrderStatus.DIKIRIM:
            raise HTTPException(status_code=400, detail="Order is not in DIKIRIM status")

        requires_rx_flag = any(item.product.requires_prescription for item in order.items)
        order = await self.repo.update_status(order, OrderStatus.SELESAI)
        
        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="CONFIRM_RECEIVED",
            module="ORDER",
            target_type="Order",
            target_id=order.id,
            new_value={"status": OrderStatus.SELESAI.value},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return OrderOut.from_orm_model(
            order=order,
            requires_prescription=requires_rx_flag,
            prescription_required_and_missing=requires_rx_flag and (not order.prescription or order.prescription.status != PrescriptionStatus.APPROVED),
            stock_deductions=[]
        )
'''

with open('app/services/order_service.py', 'r') as f:
    content = f.read()

if 'def kasir_confirm_payment' not in content:
    with open('app/services/order_service.py', 'a') as f:
        f.write(new_methods)
    print('Added missing workflow methods to order_service.py with fix')
else:
    print('Methods already exist')
