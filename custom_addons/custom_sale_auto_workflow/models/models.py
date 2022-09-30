# -*- coding: utf-8 -*-
from odoo import _, models, fields, api


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    auto_workflow_process_id = fields.Many2one("sale.workflow.process.ept", string="Workflow Process")
    payment_term_id = fields.Many2one('account.payment.term', 'Zahlungsbedingung')

class WooPaymentGateway(models.Model):
    _inherit = "woo.payment.gateway"

    def _get_payment_mode_id_domain(self):
        return [('payment_type', '=', 'inbound'), ('company_id', '=', self.env.company.id)]

    payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        domain=_get_payment_mode_id_domain,
    )


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def create(self, vals):
        payment_gateway_id = vals.get("payment_gateway_id", None)
        if payment_gateway_id:
            payment_gateway = self.env["woo.payment.gateway"].search([("id", "=", payment_gateway_id)], limit=1)
            payment_mode = payment_gateway.payment_mode_id
            if payment_mode:
                extra_vals = {"payment_mode_id": payment_mode.id}
                if payment_mode.auto_workflow_process_id:
                    extra_vals["auto_workflow_process_id"] = payment_mode.auto_workflow_process_id.id
                if payment_mode.payment_term_id:
                    extra_vals["payment_term_id"] = payment_mode.payment_term_id.id
                vals.update(extra_vals)
        return super(SaleOrder, self).create(vals)

    @api.depends("partner_id")
    def _compute_payment_mode(self):
        pass

    @api.onchange("payment_mode_id")
    def onchange_payment_mode_set_workflow(self):
        for order in self:
            if order.payment_mode_id.auto_workflow_process_id:
                order.auto_workflow_process_id = order.payment_mode_id.auto_workflow_process_id
            if order.payment_mode_id.payment_term_id:
                order.payment_term_id = order.payment_mode_id.payment_term_id

    @api.onchange("payment_gateway_id")
    def onchange_payment_gateway_id(self):
        for order in self:
            payment_mode = order.payment_gateway_id.payment_mode_id
            if payment_mode:
                order.payment_mode_id = payment_mode


class AccountMove(models.Model):
    _inherit = "account.move"

    auto_sale_order_id = fields.Many2one("sale.order", string="Auftrag")
    auto_workflow_process_id = fields.Many2one("sale.workflow.process.ept", string="Workflow Process",
                                               compute="_compute_workflow_process_id")

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AccountMove, self).create(vals_list)
        for move in records:
            order = self.env["sale.order"].search([("invoice_ids", "in", [move.id])], limit=1)
            move.auto_sale_order_id = order
        return records

    @api.depends("auto_sale_order_id")
    def _compute_workflow_process_id(self):
        self.ensure_one()
        move = self
        order = move.auto_sale_order_id
        move.auto_workflow_process_id = order.auto_workflow_process_id if order else None
