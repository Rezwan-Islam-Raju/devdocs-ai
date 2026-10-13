from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.models.workspace_model import Workspace
from app.schemas.workspace_schema import WorkspaceCreate, WorkspaceUpdate


class WorkspaceService:
    async def create(self,
                     db: AsyncSession,
                     obj_in: WorkspaceCreate,
                     owner_id: int
    ):

        db_obj = Workspace(
            name=obj_in.name,
            description=obj_in.description if obj_in.description else "",
            owner_id=owner_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_user(self, db: AsyncSession, owner_id: int, role: str) -> List[Workspace]:

        if role == "admin":
            result = await db.execute(select(Workspace))
        else:
            result = await db.execute(select(Workspace).where(Workspace.owner_id == owner_id))
        result= result.scalars().all()
        return result

    async def get_by_id(self, db: AsyncSession, workspace_id: int) -> Optional[Workspace]:


        result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
        workspace= result.scalar_one_or_none()
        return workspace

    async def update(self,
                     db: AsyncSession,
                     db_obj: Workspace,
                     obj_in: WorkspaceUpdate
    ):

        if obj_in.name is not None:
            db_obj.name = obj_in.name
        if obj_in.description is not None:
            db_obj.description = obj_in.description

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, db_obj: Workspace) :

        await db.delete(db_obj)
        await db.commit()


workspace_service = WorkspaceService()
