from sqlalchemy import *
from sqlalchemy.orm import Session
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
import json


class Base(DeclarativeBase):
    pass

class PostgresTodos(Base):
    __tablename__ = 'todos'  # Replace with your actual table name

 
    title: Mapped[str] = mapped_column(String(30))
    state: Mapped[str] = mapped_column(String(30))
    content: Mapped[str] = mapped_column(String(30))
    rawid: Mapped[int] = mapped_column(primary_key=True)
    duedate: Mapped[Integer] = mapped_column(Integer)

    def __repr__(self) -> str:
        return f"""User(rawid={self.rawid!r}, 
        title={self.title!r},
        state={self.state!r}),
        content={self.content!r},
        duedate={self.duedate!r}
        """
    
    @classmethod
    def get_number_of_entries(cls, session, asked_status='ALL'):  
        if asked_status == 'ALL':
            return session.query(cls).count()
        return session.query(cls).filter_by(state=asked_status).count()
    
    @classmethod
    def get_entries_as_json(cls, session,asked_status,asked_sortby):
        jsonarr = []
        sortedjson = []
        counter = 0

        if asked_status == "ALL":
            entries = session.query(cls)
        else:
            entries = session.query(cls).filter_by(state=asked_status)

        for entry in entries:    
            counter += 1
            jsonarr.append(json.loads(json.dumps({"id": entry.rawid, "title": f"{entry.title}", "content": f"{entry.content}", "status": f"{entry.state}", "dueDate": entry.duedate})))

        if asked_sortby == "ID":
            sortedjson = sorted(jsonarr, key=lambda y: y["id"])
        elif asked_sortby == "DUE_DATE":
            sortedjson = sorted(jsonarr, key=lambda y: y["dueDate"])
        elif asked_sortby == "TITLE":
            sortedjson = sorted(jsonarr, key=lambda y: y["title"])
        else:
            sortedjson = None

        return sortedjson, counter

    @classmethod
    def update_state_by_rawid(cls, session, rawid, new_state):
        entry = session.query(cls).filter_by(rawid=rawid).first()
        if entry:
            old_state = entry.state
            entry.state = new_state
            return old_state
        else:
            return None

    @classmethod
    def delete_by_rawid(cls, session, rawid):
        entry = session.query(cls).filter_by(rawid=rawid).first()
        if entry:
            session.delete(entry)
            return True
        else:
            return False

    @classmethod
    def create_entry(cls, session, rawid, duedate, title, content):
        # Check if the title is already taken
        if session.query(cls).filter_by(title=title).first():
            raise ValueError(True)

        new_entry = cls(
            title=title,
            state='PENDING',
            content=content,
            rawid=rawid,
            duedate=duedate
        )

        session.add(new_entry)
        return new_entry
