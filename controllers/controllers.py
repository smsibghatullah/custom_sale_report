# -*- coding: utf-8 -*-
from odoo import http

# class CustomSales(http.Controller):
#     @http.route('/custom_sales/custom_sales/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_sales/custom_sales/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_sales.listing', {
#             'root': '/custom_sales/custom_sales',
#             'objects': http.request.env['custom_sales.custom_sales'].search([]),
#         })

#     @http.route('/custom_sales/custom_sales/objects/<model("custom_sales.custom_sales"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_sales.object', {
#             'object': obj
#         })