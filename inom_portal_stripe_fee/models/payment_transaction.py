from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    stripe_fee_acknowledged = fields.Boolean(
        string='Stripe fee acknowledged',
        default=False,
        copy=False,
    )
    stripe_fee_applied = fields.Boolean(
        string='Stripe fee applied',
        default=False,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            ack_value = vals.get('stripe_fee_acknowledged', self.env.context.get('stripe_fee_acknowledged'))
            vals['stripe_fee_acknowledged'] = ack_value in (True, 'true', 'True', '1', 1, 'on')
        return super().create(vals_list)

    def _set_done(self, *args, **kwargs):
        res = super()._set_done(*args, **kwargs)
        self.filtered(lambda tx: tx.state == 'done')._apply_stripe_fee_line()
        return res

    def _apply_stripe_fee_line(self):
        for tx in self:
            if tx.stripe_fee_applied or not tx.stripe_fee_acknowledged or not tx._is_stripe():
                continue

            company = tx.company_id
            fee_product = company.stripe_card_fee_product_id
            if not fee_product:
                raise UserError(_('Please configure Stripe Card Fee Product on the company first.'))

            if tx.sale_order_ids:
                for order in tx.sale_order_ids.filtered(lambda so: so.state in ('draft', 'sent')):
                    tx._add_fee_to_sale_order(order, fee_product)

            if tx.invoice_ids:
                for move in tx.invoice_ids.filtered(lambda inv: inv.is_invoice(include_receipts=True)):
                    tx._add_fee_to_invoice(move, fee_product)

            tx.stripe_fee_applied = True

    def _is_stripe(self):
        self.ensure_one()
        provider_code = self.provider_code or self.provider_id.code
        return provider_code == 'stripe'

    def _fee_rate(self):
        self.ensure_one()
        return (self.company_id.stripe_card_fee_rate or 0.0) / 100.0

    def _compute_fee_amount(self, base_amount):
        self.ensure_one()
        return self.currency_id.round(base_amount * self._fee_rate())

    def _add_fee_to_sale_order(self, order, fee_product):
        self.ensure_one()
        amount = self._compute_fee_amount(order.amount_total)
        if amount <= 0:
            return

        existing_line = order.order_line.filtered(lambda line: line.product_id == fee_product)[:1]
        if existing_line:
            existing_line.price_unit = amount
            return

        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': fee_product.id,
            'name': fee_product.get_product_multiline_description_sale() or fee_product.display_name,
            'product_uom_qty': 1.0,
            'price_unit': amount,
        })

    def _add_fee_to_invoice(self, move, fee_product):
        self.ensure_one()
        amount = self._compute_fee_amount(move.amount_total)
        if amount <= 0 or move.state != 'draft':
            return

        existing_line = move.invoice_line_ids.filtered(lambda line: line.product_id == fee_product)[:1]
        if existing_line:
            existing_line.price_unit = amount
            return

        self.env['account.move.line'].create({
            'move_id': move.id,
            'product_id': fee_product.id,
            'name': fee_product.get_product_multiline_description_sale() or fee_product.display_name,
            'quantity': 1.0,
            'price_unit': amount,
            'tax_ids': [(6, 0, fee_product.taxes_id.filtered(lambda t: t.company_id == move.company_id).ids)],
        })
