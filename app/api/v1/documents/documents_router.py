from fastapi import APIRouter, BackgroundTasks, UploadFile, Form, Depends, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.services.document_services import document_service
from app.models.workspace_model import Workspace
from app.models.document_model import Document, DocumentStatus
from app.dependencies.auth_dependecy import require_user_id





router = APIRouter(
    tags=['Documents'],
    prefix="/api/v1/documents"
)

ALLOWED_EXTENSIONS = {"pdf", "txt", "md"}


@router.post("/upload")
async def upload_document(
        background_tasks: BackgroundTasks,
        workspace_id: int = Form(...),
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        current_user: int = Depends(require_user_id)

):


    ws_result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = ws_result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )


    if workspace.owner_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this workspace"
        )

    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""


    if file_ext not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF, TXT, MD allowed."
        )

    file_data = await file.read()

    file_size = len(file_data)

    storage_path = f"documents/workspace_{workspace_id}/{file.filename}"

    try:

        await document_service.upload_to_supabase(

            file_data=file_data,
            storage_path=storage_path,
            content_type=file.content_type
        )


        new_doc = Document(
            workspace_id=workspace_id,
            file_name=file.filename,
            file_type=file_ext,
            file_size=file_size,
            storage_path=storage_path,
            status=DocumentStatus.PENDING
        )
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)


        background_tasks.add_task(
            document_service.process_document_pipeline,
            db, new_doc.id, file_data, file_ext
        )

        return new_doc

    except Exception as e:

        await db.rollback()

        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload/Processing failed: {str(e)}"
        )
