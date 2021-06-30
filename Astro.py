from flask import Flask,render_template,url_for,redirect,abort,request,flash,g
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager,login_user,current_user,login_required,UserMixin,logout_user
from flask_paginate import Pagination, get_page_parameter
from flask_admin import Admin,BaseView,expose,AdminIndexView
from flask_admin.contrib.sqla import ModelView
from werkzeug.routing import Rule
from flask_security import login_required
from datetime import datetime
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
class AdminPage(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('AstroAdmin.html',log=False) #панель администратора
    def is_accessible(self):
        try:
            return current_user.id==1
        except:
            return abort(403)
    def inaccessible_callback(self, name, **kwargs):
        return abort(403)
admin=Admin(app,index_view=AdminPage())
class AdminView(BaseView):
    def is_accessible(self):
        return User.query.get(current_user.id).role=='admin'
    def inaccessible_callback(self, **kwargs):
        return abort(403)
class adding(AdminView): #добавление записи
    @expose('/')
    def add(self):
        return self.render('NewArticle.html',log=False,
                           admin=[i.id for i in User.query.filter_by(role='admin').all()])
class new_tag(AdminView): #добавление тега
    @expose('/')
    def add(self):
        return self.render('NewTag.html',log=False,
                           admin=[i.id for i in User.query.filter_by(role='admin').all()])
admin.add_view(adding(name='Add article',endpoint='new_article')) #шаблон для записи
admin.add_view(new_tag(name='Add tag',endpoint='new_tag')) #добавление тега
@app.route('/<int:user_id>/picture',methods=['POST'])
def new_picture(user_id): #замена аватарки
    pic=request.files['new_pic']
    path=os.path.join(app.config['UPLOAD_FOLDER'],f'user_{user_id}.jpg')
    pic.save(path)
    User.query.get(user_id).picture=f'user_{user_id}.jpg'
    db.session.commit()
    return redirect(f'/users/{user_id}')
@app.route('/<int:article_id>/delete',methods=['POST'])
def delete(article_id): #удаление записи
    data=Article.query.get(article_id)
    db.session.delete(data)
    db.session.commit()
    return redirect('/')
@app.route('/load_<string:object_>',methods=['POST'])
def load_article(object_): #загрузка записи
    if object_=='article':
        prev=request.files['preview']
        content=request.form['text']
        tags=request.form['tags'].split(',')
        pre=content[:147]+'...'
        a=Article(title=request.form['title'],preview=prev.filename,text=content,preheader=pre)
        if any([tg.title in tags for tg in Tag.query.all()]):
            a.tags.extend(db.session.query(Tag).filter(Tag.title.in_(tags)).all())
            a.preview=f'{len(Article.query.all())}.jpg'
            db.session.add(a)
            db.session.commit()
            path=os.path.join(app.config['UPLOAD_FOLDER'],f'{len(Article.query.all())}.jpg')
            prev.save(path)
            return redirect(f'/articles/{len(Article.query.all())}')
        flash('Проверьте теги')
    else:
        t=Tag(title=request.form['title'])
        db.session.add(t)
        db.session.commit()
    return redirect(f'/admin/new_{object_}')
@app.route('/articles/<int:article_id>/edit',methods=['POST'])
def edit(): #редактирование записи
    data=Article.query.get(article_id)
    data.text=request.form['content']
    db.session.commit()
    return redirect(f'/articles/{article_id}',log=True)
@app.route('/')
@app.route('/main')
def main(): #главная страница
    a=Article.query.all()[:3]
    return render_template('AstroMain.html',articles=a,cur=current_user,log=True,
                           admin=[i.id for i in User.query.filter_by(role='admin').all()])
@app.route('/articles/<int:a_id>')
def article(a_id): #запись
    if current_user.is_authenticated:
        if User.query.get(current_user.id).role=='admin':
            return render_template('AstroEdit.html',article=Article.query.get(a_id),log=True,users=User.query.all(),
                                   cur=current_user,comments=Comment.query.filter_by(article_id=a_id),
                                   admin=[i.id for i in User.query.filter_by(role='admin').all()])
    return render_template('AstroArticle.html',article=Article.query.get(a_id),log=True,cur=current_user,
                           admin=[i.id for i in User.query.filter_by(role='admin').all()],users=User.query.all(),
                           comments=Comment.query.filter_by(article_id=a_id))
@app.route('/articles/<int:article_id>/comment',methods=['POST'])
@login_required
def comment(article_id): #комментарий
    data=Comment(user_id=current_user.id,text=request.form['comment'],article_id=article_id)
    db.session.add(data)
    User.query.get(current_user.id).messages+=1
    db.session.commit()
    return redirect(f'/articles/{article_id}')
@app.route('/tags')
def tag_first(): #теги
    return render_template('AstroTags.html',tags=Tag.query.all(),cur=current_user,log=True,
                           admin=[i.id for i in User.query.filter_by(role='admin').all()])
@app.route('/tags/id=<int:tag_id>/<int:page>')
@app.route('/tags/id=<int:tag_id>')
def tag(tag_id,page=None): #записи с тегом
    if page==None:
        page=1
    data=db.session.query(Article).filter(Article.tags.contains(
        Tag.query.get(tag_id))).paginate(page,3,False)
    return render_template('AstroArticles.html',articles=data,log=True,link=f'tags/id={tag_id}/',cur_p=page,
                        admin=[i.id for i in User.query.filter_by(role='admin').all()],cur=current_user)
@app.route('/articles')
def first_page(): #первая страница с записями
    data=Article.query.paginate(1,3,False)
    return render_template('AstroArticles.html',articles=data,log=True,cur=current_user,cur_p=1,
                        admin=[i.id for i in User.query.filter_by(role='admin').all()],link='articles/page=')
@app.route('/articles/page=<int:page>')
def articles_page(page=None): #записи с пагинацией
    if page==None:
        redirect('/articles')
    data=Article.query.paginate(page,3,False)
    return render_template('AstroArticles.html',articles=data,log=True,cur=current_user,cur_p=page,
                        admin=[i.id for i in User.query.filter_by(role='admin').all()],link='articles/page=')
@app.route('/logout')
def logout():
    logout_user()
    return redirect(request.referrer)
@app.route('/users/<int:u_id>')
def profile(u_id): #страница пользователя
    return render_template('AstroUser.html',USER=User.query.get(u_id),log=True,cur=current_user,
                           admin=[i.id for i in User.query.filter_by(role='admin').all()])
@app.route('/login',methods=['POST','GET'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method=='GET':
        return render_template('AstroLog.html',log=False)
    users=User.query.filter_by(name=request.form['login']).all()
    if not users: #если список пуст
        flash('Пользователя с таким именем не существует')
        return render_template('AstroLog.html',log=False)
    checks=[check_password_hash(u.password,request.form['password']) for u in users]
    if True in checks:
        login_user(users[checks.index(True)],remember=True)
        return redirect('/')
    flash('Неверный пароль')
    return render_template('AstroLog.html',log=False)
@app.route('/sign',methods=['POST','GET'])
def sign():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method=='GET':
        return render_template('AstroSign.html',log=False)
    log=request.form['login']
    users=User.query.filter_by(name=log).all()
    checks=[check_password_hash(u.password,request.form['password']) for u in users]
    if True not in checks:
        new=User(name=log,password=generate_password_hash(request.form['password']))
        if log=='admin':
            new.role='admin'
        avatar=request.files['avatar']
        if avatar:
            path=os.path.join(app.config['UPLOAD_FOLDER'],f'user_{len(User.query.all())+1}.jpg')
            new.picture=f'user_{len(User.query.all())+1}.jpg'
        db.session.add(new)
        db.session.commit()
        return redirect('/')
    flash('Пользователь уже существует')
    return render_template('AstroSign.html',log=False)
login_manager=LoginManager(app)
login_manager.login_view = '/login'
@login_manager.user_loader #загрузка пользователя
def load_user(user_id):
    return User.query.get(user_id)
if __name__=='__main__':
    app.run(debug=True)
