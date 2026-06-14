from flask_login import UserMixin
from datetime import date, time, datetime
from sqlalchemy.orm import Mapped, mapped_column

from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id: Mapped[str] = mapped_column(db.String(64), primary_key = True)
    nickname: Mapped[str] = mapped_column(db.String(64), index = True, unique = True, nullable = False)
    email: Mapped[str] = mapped_column(db.String(120), index=True, unique=True, nullable = False)
    notes = db.relationship('Note', backref='user')

    @staticmethod
    def get(user_id):
        return User.query.get(user_id)

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User %r>' % self.nickname

notes_birds = db.Table('notes_birds',
                    db.Column('note_id', db.Integer, db.ForeignKey('birds.id')),
                    db.Column('bird_id', db.Integer, db.ForeignKey('notes.id'))
                    )

class Bird(db.Model):
    __tablename__ = 'birds'

    id: Mapped[int] = mapped_column(db.Integer, primary_key = True)
    name: Mapped[str] = mapped_column(db.String(64), index = True, unique = True, nullable = False)
    family: Mapped[str] = mapped_column(db.String(64), index = True, nullable = False)


    def __repr__(self):
        return '<Bird %r>' % self.name

class Note(db.Model):
    __tablename__ = 'notes'

    id: Mapped[int] = mapped_column(db.Integer, primary_key = True)
    text: Mapped[str] = mapped_column(db.String(2048), nullable = True)
    date_created: Mapped[datetime] = mapped_column(db.DateTime, index = True, nullable = False)
    date: Mapped[date] = mapped_column(db.Date, index = True, nullable = False)
    time: Mapped[time] = mapped_column(db.Time, index = True, nullable = False)
    geo: Mapped[str] = mapped_column(db.String(64), index = True, nullable = False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    birds = db.relationship('Bird', secondary=notes_birds, backref='notes')

    def __repr__(self):
        return f'<Note at {self.date_created!r}, {self.geo} by {self.user_id!r} with birds {self.birds!r}>'
