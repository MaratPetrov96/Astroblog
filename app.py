from flask import Flask,render_template,url_for,redirect,abort,request,flash,g,jsonify
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager,login_user,current_user,login_required,UserMixin,logout_user
from flask_paginate import Pagination
from flask_admin import Admin,BaseView,expose,AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_security import login_required
from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired,FileAllowed
from wtforms import Form,StringField,SubmitField,TextAreaField,PasswordField,TextField
from wtforms.validators import DataRequired,InputRequired
from wtforms.widgets import TextArea
import flask_whooshalchemy as whooshalchemy
import os

app=Flask(__name__,static_folder='astro')

app.config['UPLOAD_FOLDER']='astro'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///astro.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SECRET_KEY'] = 'secret key'
app.config['FLASK_ADMIN_SWATCH']='cerualen'

db=SQLAlchemy(app)

migrate = Migrate(app, db)

class User(UserMixin,db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(200), nullable=False)
    password=db.Column(db.String(150), nullable=False)
    picture=db.Column(db.String(100), default='Avatar.jpg')
    date=db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    messages=db.Column(db.Integer,nullable=False,default=0)
    role=db.Column(db.String(6),nullable=False,default='user')
    def __repr__(self):
        return self.name

table=db.Table('table',
    db.Column('article_id',db.Integer,db.ForeignKey('article.id')),
    db.Column('tag_id',db.Integer,db.ForeignKey('tag.id'))) #связь между записями и тегами

class Article(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(200), nullable=False)
    preview=db.Column(db.String(50), nullable=False)
    text=db.Column(db.Text, nullable=False)
    date=db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tags=db.relationship('Tag',backref=db.backref(
        'articles',lazy=True),lazy='dynamic',secondary=table)
    preheader=db.Column(db.String(153), nullable=False)
    def __repr__(self):
        return self.title

class Tag(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(200), nullable=False)
    def __repr__(self):
        return self.title

class Comment(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text=db.Column(db.Text, nullable=False)
    date=db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    article_id=db.Column(db.Integer,db.ForeignKey('article.id'), nullable=False)

db.create_all()
