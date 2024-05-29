from odoo import models, fields, api
from datetime import timedelta


from collections import defaultdict

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_aggregated_taxes(self):
        aggregated_taxes = defaultdict(lambda: {'amount': 0.0, 'base': 0.0})
        
        for order in self:
            for line in order.order_line:
                for tax in line.tax_id:
                    key = tax.name
                    tax_amount = tax.amount / 100.0 * line.price_unit - line.discount_amount
                    aggregated_taxes[key]['amount'] += tax_amount
                    aggregated_taxes[key]['base'] += line.price_unit - line.discount_amount
        
        return aggregated_taxes
    
   

class AccountMove(models.Model):
    _inherit = 'account.invoice'

    def get_aggregated_taxes(self):
        aggregated_taxes = defaultdict(lambda: {'amount': 0.0, 'base': 0.0})
        
        for move in self:
            for line in move.invoice_line_ids:
                for tax in line.invoice_line_tax_ids:
                    key = tax.name
                    tax_amount = tax.amount / 100.0 * (line.price_unit - line.discount_amount)
                    aggregated_taxes[key]['amount'] += tax_amount
                    aggregated_taxes[key]['base'] += line.price_unit - line.discount_amount

        
        return aggregated_taxes