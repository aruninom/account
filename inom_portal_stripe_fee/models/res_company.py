from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    stripe_card_fee_rate = fields.Float(
        string='Stripe Card Fee Rate (%)',
        default=1.5,
        help='Percentage surcharge applied when customer pays with Stripe card.',
    )
    stripe_card_fee_product_id = fields.Many2one(
        'product.product',
        string='Stripe Card Fee Product',
        help='Service product used for surcharge line creation.',
    )
