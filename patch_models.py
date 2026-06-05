import sys

notification_model = '''
class Notification(Base):
    """
    Persistent notifications for users.
    """
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False, default="info") # info, warning, error, success
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="system") # order, stock, expiry, system
    link: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship()
'''

with open('backend/app/models/models.py', 'a') as f:
    f.write(notification_model)
print("Added Notification model to models.py")
