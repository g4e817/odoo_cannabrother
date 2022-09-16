# -*- coding: utf-8 -*-
# from odoo import http


# class Postlabel(http.Controller):
#     @http.route('/postlabel/postlabel/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/postlabel/postlabel/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('postlabel.listing', {
#             'root': '/postlabel/postlabel',
#             'objects': http.request.env['postlabel.postlabel'].search([]),
#         })

#     @http.route('/postlabel/postlabel/objects/<model("postlabel.postlabel"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('postlabel.object', {
#             'object': obj
#         })
