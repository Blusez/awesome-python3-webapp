#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'kellerz zhu'  #作者
__date__ = "2017/9/10 14:41"  #创建时间

# import orm, asyncio
# from models import User, Blog, Comment



# async def test(loop):
#     await orm.create_pool(loop=loop,user='root', password='123456', db='awesome')

#     u = User(name='Test', email='test59@example.com', passwd='1234567890', image='about:blank')

#     await u.save()

# loop = asyncio.get_event_loop()
# loop.run_until_complete(test(loop))
# loop.close()

from models import User
import asyncio
import orm
import pdb
import time


# import pdb


# 测试插入


@asyncio.coroutine
def test_save(loop):
    yield from orm.create_pool(loop, user='root', password='123456', db='awesome')
    u = User(name='hi', email='hi@example.com',
             passwd='hi', image='about:blank')
    # pdb.set_trace()
    yield from u.save()

# 测试查询


@asyncio.coroutine
def test_findAll(loop):
    yield from orm.create_pool(loop, user='root', password='123456', db='awesome')
    # 这里给的关键字参数按照xxx='xxx'的形式给出，会自动分装成dict
    rs = yield from User.findAll(email='test@example.com')		# rs是一个元素为dict的list
    # pdb.set_trace()
    for i in range(len(rs)):
        print(rs[i])

# 查询条数?


@asyncio.coroutine
def test_findNumber(loop):
    yield from orm.create_pool(loop, user='root', password='123456', db='awesome')
    count = yield from User.findNumber('email')
    print(count)

# 根据主键查找，这里试ID


@asyncio.coroutine
def test_find_by_key(loop):
    yield from orm.create_pool(loop,user='root', password='123456', db='awesome')
    # rs是一个dict
    # ID请自己通过数据库查询
    rs = yield from User.find('00150546617698244db80212d534d55b0d67061e329140a000')
    print(rs)

# 根据主键删除


@asyncio.coroutine
def test_remove(loop):
    yield from orm.create_pool(loop,user='root', password='123456', db='awesome')
    # 用id初始化一个实例对象
    u = User(id='001505725136653a5b1e75a7fce498292b51a858ed8b4b8000')
    yield from u.remove()


# 根据主键更新
@asyncio.coroutine
def test_update(loop):
    yield from orm.create_pool(loop,user='root', password='123456', db='awesome')
    # 必须按照列的顺序来初始化：'update `users` set `created_at`=?, `passwd`=?, `image`=?,
    # `admin`=?, `name`=?, `email`=? where `id`=?' 注意这里要使用time()方法，否则会直接返回个时间戳对象，而不是float值
    u = User(id='001505725136653a5b1e75a7fce498292b51a858ed8b4b8000', created_at=time.time(), passwd='test',
             image='about:blank', admin=True, name='test', email='hello1@example.com')  # id必须和数据库一直，其他属性可以设置成新的值,属性要全
    # pdb.set_trace()
    yield from u.update()


loop = asyncio.get_event_loop()
loop.run_until_complete(test_remove(loop))
__pool = orm.__pool
__pool.close()  # 需要先关闭连接池
loop.run_until_complete(__pool.wait_closed())
loop.close()
