from odoo import models, fields, api
from datetime import timedelta


from collections import defaultdict

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line', 'order_line.price_total', 'order_line.price_subtotal',
             'order_line.product_uom_qty', 'discount_amount', 'discount_method',
             'discount_type', 'order_line.discount_amount', 'order_line.discount_method',
             'order_line.discount_amt')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        res_config = self.env.user.company_id

        for order in self:
            amount_untaxed = sum(line.price_subtotal for line in order.order_line)
            amount_tax = sum(line.price_tax for line in order.order_line)
            line_discount = 0.0

            for line in order.order_line:
                if line.discount_method == 'fix':
                    line_discount += line.discount_amount
                elif line.discount_method == 'per':
                    tax = line.com_tax()
                    line_discount += (line.price_subtotal + tax) * (line.discount_amount / 100)

            if order.discount_type == 'line':
                self._apply_line_discount(order, amount_untaxed, amount_tax, line_discount, res_config)
            elif order.discount_type == 'global':
                self._apply_global_discount(order, amount_untaxed, amount_tax, res_config)
            else:
                order.update({
                    'amount_untaxed': amount_untaxed,
                    'amount_tax': amount_tax,
                    'amount_total': amount_untaxed + amount_tax,
                })

    def _apply_line_discount(self, order, amount_untaxed, amount_tax, line_discount, res_config):
        if res_config.tax_discount_policy == 'tax':
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax - line_discount,
                'discount_amt_line': line_discount,
            })
        elif res_config.tax_discount_policy == 'untax':
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax - line_discount,
                'discount_amt_line': line_discount,
            })

    def _apply_global_discount(self, order, amount_untaxed, amount_tax, res_config):
        if order.discount_method == 'per':
            order_discount = (amount_untaxed + amount_tax) * (order.discount_amount / 100)
        elif order.discount_method == 'fix':
            order_discount = order.discount_amount
        else:
            order_discount = 0.0

        if res_config.tax_discount_policy == 'tax':
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax - order_discount,
                'discount_amt': order_discount,
            })
        elif res_config.tax_discount_policy == 'untax':
            sums = 0.0
            if order.discount_method == 'per':
                for line in order.order_line:
                    if line.tax_id:
                        final_discount = (order.discount_amount * line.price_subtotal) / 100.0
                        discount = line.price_subtotal - final_discount
                        taxes = line.tax_id.compute_all(discount, order.currency_id, 1.0, product=line.product_id, partner=order.partner_id)
                        sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
            elif order.discount_method == 'fix':
                for line in order.order_line:
                    if line.tax_id:
                        final_discount = (order.discount_amount * line.price_subtotal) / amount_untaxed
                        discount = line.price_subtotal - final_discount
                        taxes = line.tax_id.compute_all(discount, order.currency_id, 1.0, product=line.product_id, partner=order.partner_id)
                        sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))

            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': sums,
                'amount_total': amount_untaxed + sums - order_discount,
                'discount_amt': order_discount,
            })

         
    def subtract_discount_from_tax(self):
       
        if self.env.context.get('skip_subtract_discount_from_tax'):
            return
       
        for order in self:
            total_tax = 0 
            discount_amt = 0
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

            order.with_context(skip_subtract_discount_from_tax=True).update({
                'amount_tax': total_tax,
                'amount_total': total_tax + order.amount_untaxed 
                })

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
                    if line.discount_method == 'fix':
                        price_after_discount = (line.price_unit * line.quantity) - line.discount_amount
                    elif line.discount_method == 'per':
                        price_after_discount = (line.price_unit * line.quantity) * (1 - (line.discount_amount or 0.0) / 100.0)
                    else:
                        price_after_discount = line.price_unit * line.quantity

                    taxes = line.invoice_line_tax_ids.compute_all(price_after_discount, move.currency_id, 1, product=line.product_id, partner=move.partner_id)

                    for tax in line.invoice_line_tax_ids:
                        key = tax.name
                        tax_amount = tax.amount / 100.0 * price_after_discount
                        aggregated_taxes[key]['amount'] += tax_amount
                        aggregated_taxes[key]['base'] += price_after_discount

            return aggregated_taxes

    def subtract_discount_from_tax(self):
            if self.env.context.get('skip_subtract_discount_from_tax'):
                return
            for move in self:
                total_tax = 0
                discount_amt = 0
                for line in move.invoice_line_ids:
                    if line.discount_method == 'fix':
                        price_after_discount = (line.price_unit * line.quantity) - line.discount_amount
                    elif line.discount_method == 'per':
                        price_after_discount = (line.price_unit * line.quantity) * (1 - (line.discount_amount or 0.0) / 100.0)
                    else:
                        price_after_discount = line.price_unit * line.quantity

                    taxes = line.invoice_line_tax_ids.compute_all(price_after_discount, move.currency_id, 1, product=line.product_id, partner=move.partner_id)

                    line.update({
                        'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                        'price_total': taxes['total_included'],
                        'price_subtotal': taxes['total_excluded'],
                    })

                    for tax in line.invoice_line_tax_ids:
                        tax_amount = tax.amount / 100.0 * price_after_discount
                        total_tax += tax_amount

                move.with_context(skip_subtract_discount_from_tax=True).update({
                    'amount_tax': total_tax,
                    'amount_total': total_tax + move.amount_untaxed - discount_amt,
                })

    @api.model
    def create(self, vals):
            invoice = super(AccountMove, self).create(vals)
            invoice.subtract_discount_from_tax()
            return invoice

    def write(self, vals):
            res = super(AccountMove, self).write(vals)
            self.subtract_discount_from_tax()
            return res