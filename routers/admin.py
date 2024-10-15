from fastapi import APIRouter, Depends, HTTPException
from auth import check_admin_privileges
from database import SQLiteDataBase, User, Note, NoteBase
from sqlmodel import Session, select
from typing import Annotated


db = SQLiteDataBase(db_name="db.db", connect_args={"check_same_thread": False})
SessionDep = Annotated[Session, Depends(db.get_session)]

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"],
    dependencies=[Depends(check_admin_privileges)],
    responses={404: {"description": "Not found"}},
)


@router.patch("/notes/{note_id}")
def restore_note(note_id: int, session: SessionDep):
    note = session.exec(select(Note).where(Note.id == note_id)).one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.sqlmodel_update({"is_deleted": False})
    session.add(note)
    session.commit()
    session.refresh(note)
    return NoteBase.model_validate(note)


@router.get("/notes/")
def read_notes(session: SessionDep) -> list[NoteBase]:
    notes = session.exec(select(Note).where(Note.is_deleted == False)).all()
    notes_db = [NoteBase.model_validate(note) for note in notes]
    return notes_db


@router.get("/notes/{note_id}")
def read_note(note_id: int, session: SessionDep) -> NoteBase:
    note = session.exec(select(Note).where(Note.id == note_id, Note.is_deleted == False)).one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteBase.model_validate(note)


@router.get("/user_notes/{user_id}")
def read_note(user_id: int, session: SessionDep) -> list[NoteBase]:
    notes = session.exec(select(Note).where(Note.user_id == user_id, Note.is_deleted == False)).all()
    if not notes:
        raise HTTPException(status_code=404, detail="Note not found")
    return [NoteBase.model_validate(note) for note in notes]