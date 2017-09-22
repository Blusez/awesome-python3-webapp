#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'kellerz zhu'

' url handlers '
# 后端API包括：

# 获取日志：GET /api/blogs

# 创建日志：POST /api/blogs

# 修改日志：POST /api/blogs/:blog_id

# 删除日志：POST /api/blogs/:blog_id/delete

# 获取评论：GET /api/comments

# 创建评论：POST /api/blogs/:blog_id/comments

# 删除评论：POST /api/comments/:comment_id/delete

# 创建新用户：POST /api/users

# 获取用户：GET /api/users

# 管理页面包括：

# 评论列表页：GET /manage/comments

# 日志列表页：GET /manage/blogs

# 创建日志页：GET /manage/blogs/create

# 修改日志页：GET /manage/blogs/

# 用户列表页：GET /manage/users

# 用户浏览页面包括：

# 注册页：GET /register

# 登录页：GET /signin

# 注销页：GET /signout

# 首页：GET /

# 日志详情页：GET /blog/:blog_id

import re, time, json, logging, hashlib, base64, asyncio

from web_frame import get, post

from config import configs

import logging; logging.basicConfig(level=logging.INFO)

from models import User, Comment, Blog, next_id

from apis import Page, APIValueError, APIResourceNotFoundError, APIError,APIPermissionError

from aiohttp import web
import markdown2

# email的匹配正则表达式
_RE_EMAIL = re.compile(
    r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
# 密码的匹配正则表达式
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

# 首页，显示blog列表
@get('/')
async def index(*, page='1'):
    # 获取到要展示的博客页数是第几页
    page_index = get_page_index(page)
    # 查找博客表里的条目数
    num = await Blog.findNumber('count(id)')
    # 通过Page类来计算当前页的相关信息
    page = Page(num, page_index)
    # p = Page(num, page_index, item_page=configs.blog_item_page, page_show=configs.page_show)
     
    
    # 如果表里没有条目，则不需要
    if num == 0:
        blogs = []
    else:
        # 否则，根据计算出来的offset(取的初始条目index)和limit(取的条数)，来取出条目
        blogs = await Blog.findAll(orderBy='created_at desc', limit=(page.offset, page.limit))
        # 返回给浏览器
    return {
        '__template__': 'blogs.html',
        'page': page,
        'blogs': blogs
    }
    # users = await User.findAll()
    # return {
    #     '__template__': 'test.html',
    #     'users': users
    # }
    # summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    # blogs = [
    #     Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
    #     Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
    #     Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    # ]
    # return {
    #     '__template__': 'blogs.html',
    #     'blogs': blogs
    # }
# test
# @get('/api/users')
# async def api_get_users():
#     users = await User.findAll(orderBy='created_at desc')
#     for u in users:
#         u.passwd = '******'
#     return dict(users=users)


# 检测当前用户是不是admin用户


def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError(" NOT ADMIN")

# 获取页数，主要是做一些容错处理


def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p
# 根据用户信息拼接一个cookie字符串


def user2cookie(user, max_age):
    # build cookie string by: id-expires-sha1
    # 过期时间是当前时间+设置的有效时间
    expires = str(int(time.time() + max_age))
    # 构建cookie存储的信息字符串
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    # 用-隔开，返回
    return '-'.join(L)

# 绑定登录信息


# 根据cookie字符串，解析出用户信息相关的


@asyncio.coroutine
def cookie2user(cookie_str):
    # cookie_str是空则返回
    if not cookie_str:
        return None
    try:
        # 通过'-'分割字符串
        L = cookie_str.split('-')
        # 如果不是3个元素的话，与我们当初构造sha1字符串时不符，返回None
        if len(L) != 3:
            return None
        # 分别获取到用户id，过期时间和sha1字符串
        uid, expires, sha1 = L
        # 如果超时，返回None
        if int(expires) < time.time():
            return None
        # 根据用户id查找库，对比有没有该用户
        user = yield from User.find(uid)
        # 没有该用户返回None
        if user is None:
            return None
        # 根据查到的user的数据构造一个校验sha1字符串
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        # 比较cookie里的sha1和校验sha1，一样的话，说明当前请求的用户是合法的
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        # 返回合法的user
        return user
    except Exception as e:
        logging.exception(e)
        return None

# 登陆页面


@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }

# 登出操作


@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    # 清理掉cookie得用户信息数据
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out')
    return r

# 注册界面
@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }

# 注册请求


@post('/api/users')
async def api_register_user(*, email, name, passwd):
    # 判断name是否存在，且是否只是'\n', '\r',  '\t',  ' '，这种特殊字符
    if not name or not name.strip():
        raise APIValueError('name')
    # 判断email是否存在，且是否符合规定的正则表达式
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    # 判断passwd是否存在，且是否符合规定的正则表达式
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')

    # 查一下库里是否有相同的email地址，如果有的话提示用户email已经被注册过
    users = await User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')

    # 生成一个当前要注册用户的唯一uid
    uid = next_id()
    # 构建shal_passwd
    sha1_passwd = '%s:%s' % (uid, passwd)

    admin = False
    if email == 'admin@163.com':
        admin = True

    # 创建一个用户（密码是通过sha1加密保存）
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
                image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest(), admin=admin)

# 保存这个用户到数据库用户表
    await user.save()
    logging.info('save user OK')
    # 构建返回信息
    r = web.Response()
    # 添加cookie
    r.set_cookie(COOKIE_NAME, user2cookie(
        user, 86400), max_age=86400, httponly=True)
    # 只把要返回的实例的密码改成'******'，库里的密码依然是正确的，以保证真实的密码不会因返回而暴漏
    user.passwd = '******'
    # 返回的是json数据，所以设置content-type为json的
    r.content_type = 'application/json'
    # 把对象转换成json格式返回
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


# 登陆请求


@post('/api/authenticate')
async def authenticate(*, email, passwd):
    # 如果email或passwd为空，都说明有错误
    if not email:
        raise APIValueError('email', 'Invalid email')
    if not passwd:
        raise APIValueError('passwd', 'Invalid  passwd')
    # 根据email在库里查找匹配的用户
    users = await User.findAll('email=?', [email])
    # 没找到用户，返回用户不存在
    if len(users) == 0:
        raise APIValueError('email', 'email not exist')
    # 取第一个查到用户，理论上就一个
    user = users[0]
    # 按存储密码的方式获取出请求传入的密码字段的sha1值
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    # 和库里的密码字段的值作比较，一样的话认证成功，不一样的话，认证失败
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid passwd')
    # 构建返回信息
    r = web.Response()
    # 添加cookie
    r.set_cookie(COOKIE_NAME, user2cookie(
        user, 86400), max_age=86400, httponly=True)
    # 只把要返回的实例的密码改成'******'，库里的密码依然是正确的，以保证真实的密码不会因返回而暴漏
    user.passwd = '******'
    # 返回的是json数据，所以设置content-type为json的
    r.content_type = 'application/json'
    # 把对象转换成json格式返回
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r
# ---------------------------------------评论管理---------------------------------------
# 评论管理页面
@get('/manage/')
def manage():
    return 'redirect:/manage/comments'

@get('/manage/comments')
def manage_comments(*, page='1'):
    # 查看所有评论
    return {
        '__template__': 'manage_comments.html',
        'page_index': get_page_index(page)
    }

@get('/api/comments')
async def api_comments(*, page='1'):
    # 根据page获取评论，注释可参考 index 函数的注释，不细写了
    page_index = get_page_index(page)
    num = await Comment.findNumber('count(id)')
    p = Page(num, page_index)
    
    if num == 0:
        return dict(page=p, comments=())
    comments = await Comment.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)

@post('/api/blogs/{id}/comments')
async def api_create_comment(id, request, *, content):
    # 对某个博客发表评论
    user = request.__user__
    # 必须为登陆状态下，评论
    if user is None:
        raise APIPermissionError('content')
    # 评论不能为空
    if not content or not content.strip():
        raise APIValueError('content')
    # 查询一下博客id是否有对应的博客
    blog = await Blog.find(id)
    # 没有的话抛出错误
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    # 构建一条评论数据
    comment = Comment(blog_id=blog.id, user_id=user.id, user_name=user.name,
                      user_image=user.image, content=content.strip())
    # 保存到评论表里
    await comment.save()
    return comment

@post('/api/comments/{id}/delete')
async def api_delete_comments(id, request):
    # 删除某个评论
    logging.info(id)
    # 先检查是否是管理员操作，只有管理员才有删除评论权限
    check_admin(request)
    # 查询一下评论id是否有对应的评论
    c = await Comment.find(id)
    # 没有的话抛出错误
    if c is None:
        raise APIResourceNotFoundError('Comment')
    # 有的话删除
    await c.remove()
    return dict(id=id)

# -----------------------------------------------------用户管理------------------------------------

@get('/show_all_users')
async def show_all_users():
    # 显示所有的用户
    users = await User.findAll()
    logging.info('to index...')
    # return (404, 'not found')

    return {
        '__template__': 'test.html',
        'users': users
    }

#       page_index = get_page_index(page)
#     num = await Comment.findNumber('count(id)')
#     p = Page(num, page_index)
#     if num == 0:
#         return dict(page=p, comments=())
#     comments = await Comment.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
#     return dict(page=p, comments=comments)
@get('/api/users')
async def api_get_users(*,page=1):
    # 获取当前要展示的页数
    page_index = get_page_index(page)
    num = await User.findNumber('count(id)')
    p = Page(num,page_index)
    if num ==0:
        return dict(page=p,users=())
    # 返回用户信息jason格式
    users = await User.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    logging.info('users = %s and type = %s' % (users, type(users)))
    for u in users:
        u.passwd = '******'
    return dict(page=p, users=users)

@get('/manage/users')
def manage_users(*, page='1'):
    # 查看所有用户
    return {
        '__template__': 'manage_users.html',
        'page_index': get_page_index(page)
    }


# ------------------------------------------博客管理的处理函数----------------------------------


@get('/manage/blogs/create')
def manage_create_blog():
    # 写博客页面
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'  # 对应HTML页面中VUE的action名字
    }

@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    # 上传博客
    # 只有管理员可以写博客
    check_admin(request)
    # name，summary,content 不能为空
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty')

    # 根据传入的信息，构建一条博客数据
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name,
                user_image=request.__user__.image, name=name.strip(), summary=summary.strip(), content=content.strip())
    # 保存
    await blog.save()
    return blog

@get('/manage/blogs')
def manage_blogs(*, page='1'):
    # 博客管理页面
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page)
    }

@get('/api/blogs')
async  def api_blogs(*, page='1'):
    # 获取博客信息
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)
 

 # 把存文本文件转为html格式的文本


def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<',
                                                                        '&lt;').replace('>', '&gt;'), filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)

@get('/blog/{id}')
async def get_blog(id):
    # 根据博客id查询该博客信息
    blog = await Blog.find(id)
    # 根据博客id查询该条博客的评论
    comments = await Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    # markdown2是个扩展模块，这里把博客正文和评论套入到markdonw2中
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    # 返回页面
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }

# 修改博客流程

# 获取界面
@get('/manage/blogs/modify/{id}')
def manage_modify_blog(id):
    # 修改博客的页面
    return {
        '__template__': 'manage_blog_modify.html',
        'id': id,
        'action': '/api/blogs/modify'
    }

# 获取该博客信息
@get('/api/blogs/{id}')
async def api_get_blog(*, id):
    # 获取某条博客的信息
    blog = await Blog.find(id)
    return blog

@post('/api/blogs/modify')
async def api_modify_blog(request, *, id, name, summary, content):
     # 修改一条博客
    logging.info("修改的博客的博客ID为：%s", id)
    # name，summary,content 不能为空
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty')

    # 获取指定id的blog的数据
    blog = await Blog.find(id)
    blog.name = name
    blog.summary = summary
    blog.content = content

    # 保存
    await blog.update();
    # api必须返回json
    return blog 

# 删除一条博客
@post('/api/blogs/{id}/delete')
async def api_delete_blog(id, request):
    # 删除一条博客
    logging.info("删除博客的博客ID为：%s" % id)
    # 先检查是否是管理员操作，只有管理员才有删除评论权限
    check_admin(request)
    # 查询一下评论id是否有对应的评论
    comments = await Comment.findAll('blog_id = ?',[id])

    # 删除所有相关评论
    for c in comments:
        await c.remove()
    # 查询相关的blog
    b = await Blog.find(id)
    # 没有的话抛出错误
    if b is None:
        raise APIResourceNotFoundError('Comment')
    # 有的话删除
    await b.remove()
    logging.info("删除成功")
    return dict(id=id)