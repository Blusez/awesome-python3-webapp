import json
import logging
import inspect
import functools

# 简单的几个api错误异常类，用于跑出异常


class APIError(Exception):

    def __init__(self, error, data='', message=''):
        super(APIError, self).__init__(message)
        self.error = error
        self.data = data
        self.message = message


class APIValueError(APIError):

    """docstring for APIValueError"""

    def __init__(self, field, message=''):
        super(APIValueError, self).__init__('value:invalid', field, message)


class APIResourceNotFoundError(APIError):

    """docstring for APIResourceNotFoundError"""

    def __init__(self,  field, message=''):
        super(APIResourceNotFoundError, self).__init__(
            'value:notfound', field, message)


class APIPermissionError(APIError):

    """docstring for APIPermissionError"""

    def __init__(self, message=''):
        super(APIPermissionError, self).__init__(
            'permission:forbidden', 'permission', message)


# 用于分页
class Page(object):

    """docstring for Page"""
    # 参数说明：
    # item_count：要显示的条目数量
    # page_index：要显示的是第几页
    # page_size：每页的条目数量，为了方便测试现在显示为2条

    def __init__(self, item_count, page_index=1, page_size=3):
        self.item_count = item_count
        self.page_size = page_size
        # 计算出应该有多少页才能显示全部的条目
        self.page_count = item_count // page_size + \
            (1 if item_count % page_size > 0 else 0)
        # 如果没有条目或者要显示的页超出了能显示的页的范围
        if (item_count == 0) or (page_index > self.page_count):
            # 则不显示
            self.offset = 0
            self.limit = 0
            self.page_index = 1
        else:
            # 否则说明要显示
            # 设置显示页就是传入的要求显示的页
            self.page_index = page_index
            # 这页的初始条目的offset
            self.offset = self.page_size * (page_index - 1)
            # 这页能显示的数量
            self.limit = self.page_size
        # 这页后面是否还有下一页
        self.has_next = self.page_index < self.page_count
        # 这页之前是否还有上一页
        self.has_previous = self.page_index > 1

    def __str__(self):
        return 'item_count: %s, page_count: %s, page_index: %s, page_size: %s, offset: %s, limit: %s' % (self.item_count, self.page_count, self.page_index, self.page_size, self.offset, self.limit)

    __repr__ = __str__
# class Page(object):
#     '''
#     Page object for display pages.
#     '''

#     def __init__(self, item_count, page_index=1, item_page=2, page_show=2):
        

#         '''
#         Init Pagination by item_count, page_index and item_page.
#         item_count:总数
#         page_index：当前页
#         item_page：一页显示多少
#         page_show：页数显示数量

#         >>> p1 = Page(100, 1)
#         >>> p1.page_count
#         10
#         >>> p1.offset
#         0
#         >>> p1.limit
#         10
#         >>> p2 = Page(90, 9, 10)
#         >>> p2.page_count
#         9
#         >>> p2.offset
#         80
#         >>> p2.limit
#         10
#         >>> p3 = Page(91, 10, 10)
#         >>> p3.page_count
#         10
#         >>> p3.offset
#         90
#         >>> p3.limit
#         10
#         '''
#         self.item_count = item_count
#         self.item_page = item_page
#         self.page_count = item_count // item_page + (1 if item_count % item_page > 0 else 0)
#         self.page_show = page_show - 2    # 去掉始终显示的首页和末页的两项
#         if (item_count == 0) or (page_index > self.page_count):
#             self.offset = 0
#             self.limit = 0
#             self.page_index = 1
#         else:
#             self.page_index = page_index
#             self.offset = self.item_page * (page_index - 1)
#             self.limit = self.item_page
#         self.has_next = self.page_index < self.page_count
#         self.has_pre = self.page_index > 1

#     def __str__(self):
#         return 'item_count: %s, page_count: %s, page_index: %s, item_page: %s, offset: %s, limit: %s' % \
#             (self.item_count, self.page_count, self.page_index, self.item_page, self.offset, self.limit)

#     __repr__ = __str__

#     @classmethod
#     def page2int(cls, str):
#         p = 1
#         try:
#             p = int(str)
#         except ValueError:
#             pass
#         if p < 1:
#             p = 1
#         return p

#     def pagelist(self):
#         left = 2
#         right = self.page_count

#         if (self.page_count > self.page_show):
#             left = self.page_index - (self.page_show // 2)
#             if (left < 2):
#                 left = 2
#             right = left + self.page_show
#             if (right > self.page_count):
#                 right = self.page_count
#                 left = right - self.page_show
#         # 生成的列表不含首页和末页
#         self.pagelist = list(range(left, right))
#         return list(range(left, right))

