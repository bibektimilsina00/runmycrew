from sqlmodel import SQLModel


class ExecutionLogOut(SQLModel):
    id: str
    t: str
    lvl: str
    src: str
    msg: str
