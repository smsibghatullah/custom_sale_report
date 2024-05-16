from odoo import models, fields, api
from datetime import timedelta


import logging

_logger = logging.getLogger(__name__)

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'