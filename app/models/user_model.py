from enum import Enum as PyEnum

from sqlalchemy import (Boolean,Column,DateTime,Enum,Integer,String,func)
from sqlalchemy.orm import relationship

from app.database.session import Base


class UserRole(str, PyEnum):
    USER = "user"
    ADMIN = "admin"


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True,index=True)

    name = Column(String(100),nullable=False)

    email = Column(String(255),unique=True,nullable=False,index=True )

    password_hash = Column(String(255), nullable=False)

    role = Column(Enum(UserRole),default=UserRole.USER,nullable=False)

    is_active = Column(Boolean,default=True,nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationship with workspaces

    workspaces = relationship("Workspace", back_populates="owner", cascade="all, delete-orphan")

