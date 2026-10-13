from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.session import get_db
from app.dependencies.auth_dependecy import require_user_id
from app.schemas.workspace_schema import MessageResponse
from app.schemas.workspace_schema import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
from app.services.workspace_services import workspace_service

router = APIRouter(tags=['Workspaces'], prefix="/api/v1/workspaces")



@router.post("/",
     response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_new_workspace(
        workspace_in: WorkspaceCreate,
        db: AsyncSession = Depends(get_db),
        current_user: int = Depends(require_user_id)
):


    result= await workspace_service.create(
        db=db, obj_in=workspace_in,
        owner_id=current_user
    )
    return result



@router.get("/", response_model=List[WorkspaceResponse])
async def list_all_workspaces(
        db: AsyncSession = Depends(get_db),
        current_user: int = Depends(require_user_id)

):

    result= await workspace_service.get_by_user(
        db=db,
        owner_id=current_user,
        role="user"
    )

    return result


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace_details(
        workspace_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: int = Depends(require_user_id)
):
    workspace = await workspace_service.get_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )


    if workspace.owner_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Access denied to this workspace"
        )

    return workspace



@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_existing_workspace(
        workspace_id: int,
        workspace_in: WorkspaceUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: int = Depends(require_user_id)

):
    workspace = await workspace_service.get_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )


    if workspace.owner_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to update"
        )

    result= await workspace_service.update(
        db=db,
        db_obj=workspace,
        obj_in=workspace_in
    )
    return result


@router.delete("/{workspace_id}", response_model=MessageResponse)
async def delete_existing_workspace(
        workspace_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: int = Depends(require_user_id)
):
    workspace = await workspace_service.get_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )


    if workspace.owner_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to delete"
        )

    await workspace_service.delete(
        db=db,
        db_obj=workspace
    )
    return {"message": "Workspace deleted successfully"}
