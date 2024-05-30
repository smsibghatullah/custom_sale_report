from odoo import models, fields, api
from datetime import timedelta


from collections import defaultdict

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def subtract_discount_from_tax(self):
        if self.env.context.get('skip_subtract_discount_from_tax'):
            return
        for order in self:
            total_tax = 0 
            for line in order.order_line:
                if line.discount_method == 'fix':
                    price_after_discount = (line.price_unit * line.product_uom_qty) - line.discount_amount
                elif line.discount_method == 'per':
                    price_after_discount = (line.price_unit * line.product_uom_qty) * (1 - (line.discount_amount or 0.0) / 100.0)
                    discount_amt = (line.price_unit * line.product_uom_qty) - price_after_discount
                else:
                    price_after_discount = line.price_unit * line.product_uom_qty
                    discount_amt = 0.0

                taxes = line.tax_id.compute_all(price_after_discount, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_shipping_id)

                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })

                for tax in line.tax_id:
                    tax_amount = tax.amount / 100.0 * price_after_discount
                    total_tax += tax_amount

            order.with_context(skip_subtract_discount_from_tax=True).update({'amount_tax': total_tax})

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order.subtract_discount_from_tax()
        return order

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self.subtract_discount_from_tax()
        return res


    def get_aggregated_taxes(self):
            aggregated_taxes = defaultdict(lambda: {'amount': 0.0, 'base': 0.0})

            for order in self:
                for line in order.order_line:
                    if line.discount_method == 'fix':
                        price_after_discount = (line.price_unit * line.product_uom_qty) - line.discount_amount
                    elif line.discount_method == 'per':
                        price_after_discount = (line.price_unit * line.product_uom_qty) * (1 - (line.discount_amount or 0.0) / 100.0)
                        discount_amt = (line.price_unit * line.product_uom_qty) - price_after_discount
                    else:
                        price_after_discount = line.price_unit * line.product_uom_qty
                        discount_amt = 0.0

                    taxes = line.tax_id.compute_all(price_after_discount, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_shipping_id)

                    for tax in line.tax_id:
                        key = tax.name
                        tax_amount = tax.amount / 100.0 * price_after_discount
                        aggregated_taxes[key]['amount'] += tax_amount
                        aggregated_taxes[key]['base'] += price_after_discount

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
    
