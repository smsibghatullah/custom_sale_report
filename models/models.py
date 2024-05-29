from collections import defaultdict

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_aggregated_taxes(self):
        aggregated_taxes = defaultdict(lambda: {'amount': 0.0, 'base': 0.0})
        
        for order in self:
            for line in order.order_line:
                for tax in line.tax_id:
                    key = tax.name
                    tax_amount = tax.amount / 100.0 * line.price_unit
                    aggregated_taxes[key]['amount'] += tax_amount
                    aggregated_taxes[key]['base'] += line.price_unit
        
        return aggregated_taxes
