import sys

new_method = '''
    async def upload_payment_proof(
        self,
        order_id: int,
        file: UploadFile,
        current_user: User,
        request: Request,
    ) -> OrderOut:
        """
        Upload a payment proof image for a specific order.
        """
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id={order_id} not found.",
            )

        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload payment proofs for your own orders.",
            )

        if order.status != OrderStatus.MENUNGGU_PEMBAYARAN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot upload payment proof when order status is {order.status.value}.",
            )

        # MIME type validation
        content_type = file.content_type or ""
        if content_type not in _ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported image type '{content_type}'. "
                    f"Allowed types: {sorted(_ALLOWED_IMAGE_TYPES)}."
                ),
            )

        # File size validation (Max 5MB)
        image_bytes = await file.read()
        max_bytes = 5 * 1024 * 1024
        if len(image_bytes) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Image file too large ({len(image_bytes) / 1024 / 1024:.1f} MB). "
                    f"Maximum is 5 MB."
                ),
            )

        # Build path
        ext = Path(file.filename or "").suffix.lower()
        if not ext or ext not in _ALLOWED_IMAGE_EXTENSIONS:
            ext = mimetypes.guess_extension(content_type) or ".jpg"
            ext = ".jpg" if ext == ".jpe" else ext

        upload_root = Path(settings.UPLOAD_DIR)
        proof_dir = upload_root / "payments" / str(order.id)
        proof_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4()}{ext}"
        file_path = proof_dir / filename

        # Write
        file_path.write_bytes(image_bytes)
        relative_url = f"payments/{order.id}/{filename}"

        # DB Insert / Update
        order = await self.repo.update_payment_proof(order, relative_url)
        order = await self.repo.update_status(order, OrderStatus.MENUNGGU_KONFIRMASI_KASIR)

        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="UPLOAD_PAYMENT_PROOF",
            module="ORDER",
            target_type="Order",
            target_id=order.id,
            new_value={"payment_proof_url": relative_url, "status": OrderStatus.MENUNGGU_KONFIRMASI_KASIR.value},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        requires_rx_flag = any(item.product.requires_prescription for item in order.items)
        return OrderOut.from_orm_model(
            order=order,
            requires_prescription=requires_rx_flag,
            prescription_required_and_missing=requires_rx_flag and (not order.prescription or order.prescription.status != PrescriptionStatus.APPROVED),
            stock_deductions=[]
        )
'''

with open('app/services/order_service.py', 'r') as f:
    content = f.read()

if 'def upload_payment_proof' not in content:
    with open('app/services/order_service.py', 'a') as f:
        f.write(new_method)
    print('Added method to order_service.py')
else:
    print('Method already exists')
