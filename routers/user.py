from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from database import SQLiteDataBase, User, Note, NoteBase
from sqlmodel import Session, select
from typing import Annotated


db = SQLiteDataBase(db_name="db.db", connect_args={"check_same_thread": False})
SessionDep = Annotated[Session, Depends(db.get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.post("/notes")
def create_note(note: NoteBase, session: SessionDep, current_user: CurrentUser):
    note_db = Note(title=note.title, body=note.body, user_id=current_user.id)
    session.add(note_db)
    session.commit()
    session.refresh(note_db)
    return note_db


@router.put("/notes/{note_id}")
def update_note(note_id: int, notebase: NoteBase, session: SessionDep, current_user: CurrentUser):
    note = session.exec(select(Note).where(Note.id == note_id, Note.is_deleted == False)).one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    note_data = notebase.model_dump(exclude_unset=True)
    note.sqlmodel_update(note_data)
    session.add(note)
    session.commit()
    session.refresh(note)
    return NoteBase.model_validate(note)


@router.patch("/notes/{note_id}")
def delete_note(note_id: int, session: SessionDep, current_user: CurrentUser):
    note = session.exec(select(Note).where(Note.id == note_id)).one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    note.sqlmodel_update({"is_deleted": True})
    session.add(note)
    session.commit()
    session.refresh(note)
    return {"ok": True}


@router.get("/notes/")
def read_notes(session: SessionDep, current_user: CurrentUser) -> list[NoteBase]:
    notes = session.exec(select(Note).where(Note.user_id == current_user.id, Note.is_deleted == False)).all()
    notes_db = [NoteBase.model_validate(note) for note in notes]
    return notes_db


@router.get("/notes/{note_id}")
def read_note(note_id: int, session: SessionDep, current_user: CurrentUser) -> NoteBase:
    note = session.exec(select(Note).where(Note.id == note_id, Note.is_deleted == False)).one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return NoteBase.model_validate(note)
