from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=True
    )

    password_hash = db.Column(
        db.String(128),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Watchlist(db.Model):
    __tablename__ = "watchlist"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    movie_id = db.Column(
        db.Integer,
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )


class Watched(db.Model):
    __tablename__ = "watched"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    movie_id = db.Column(
        db.Integer,
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )