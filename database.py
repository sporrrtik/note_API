from sqlmodel import Field, Session, SQLModel, create_engine, select
from dependencies import get_password_hash


class SQLiteDataBase:
    def __init__(self, db_name, connect_args):
        self.db_name = db_name
        self.connect_args = connect_args
        self.engine = self.create_engine()

    def create_engine(self):
        return create_engine(f"sqlite:///{self.db_name}", connect_args=self.connect_args)

    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        with Session(self.engine) as session:
            yield session

    def create_base_users(self):
        with Session(self.engine) as session:
            if not session.exec(select(User)).all():
                user1 = User(username="Admin", hashed_password=get_password_hash("admin"), is_admin=True)
                user2 = User(username="User1", hashed_password=get_password_hash("user"))
                user3 = User(username="User2", hashed_password=get_password_hash("user"))

                session.add(user1)
                session.add(user2)
                session.add(user3)

                session.commit()
                print("Base users were created")

    def get_user(self, username):
        with Session(self.engine) as session:
            return session.exec(select(User).where(User.username == username)).one_or_none()


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    hashed_password: str
    is_admin: bool | None = False


class NoteBase(SQLModel):
    title: str = Field(max_length=256)
    body: str = Field(max_length=65536)


class Note(NoteBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    is_deleted: bool | None = False