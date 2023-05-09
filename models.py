from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)


class Lists(db.Model):
    __tablename__ = 'lists'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    u_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cards = db.relationship('Cards', backref='card')


class Cards(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.String)
    time_created = db.Column(db.DateTime)
    time_updated = db.Column(db.DateTime)
    time_completed = db.Column(db.DateTime, default=None)
    deadline = db.Column(db.String)
    l_id = db.Column(db.Integer, db.ForeignKey('lists.id'), nullable=False)
