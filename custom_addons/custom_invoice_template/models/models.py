# -*- coding: utf-8 -*-
import base64

from odoo import _, models, fields, api


class AccountMoveSequence(models.Model):
    _inherit = "account.move"

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'invoice_date' in vals:
                current_date = fields.Datetime.to_datetime(vals['invoice_date'])
            else:
                current_date = fields.Datetime.today()
            seq_date = fields.Datetime.context_timestamp(self, current_date)

            vals['name'] = self.env['ir.sequence'].next_by_code('account.move', sequence_date=seq_date) or _('New')
            vals['payment_reference'] = vals['name']
        return super(AccountMoveSequence, self).create(vals)


class PostlabelInstantAssignUser(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def create(self, vals):
        stock = super(PostlabelInstantAssignUser, self).create(vals)
        stock.action_assign_user()
        return stock
