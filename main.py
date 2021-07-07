from app import *
from Admin import *

admin=Admin(app,index_view=AdminPage())
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
            return render_template('AstroEdit.html',article=Article.query.get(a_id),log=True,cur=current_user,
                                   comments=db.session.query(User,Comment,Article).filter(User.id==Comment.user_id,
                                    Comment.article_id==Article.id).filter(Article.id==a_id).all(),
                                   admin=[i.id for i in User.query.filter_by(role='admin').all()])
    return render_template('AstroArticle.html',article=Article.query.get(a_id),log=True,cur=current_user,
                           admin=[i.id for i in User.query.filter_by(role='admin').all()],comments=db.session.query(
                               User,Comment,Article).filter(User.id==Comment.user_id,Comment.article_id==Article.id
                            ).filter(Article.id==a_id).all())

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

@app.route('/test')
def test():
    return render_template('Test.html',text=type(request.remote_addr))

if __name__=='__main__':
    app.run(debug=True)
