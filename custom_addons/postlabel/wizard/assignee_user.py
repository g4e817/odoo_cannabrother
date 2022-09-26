from odoo import fields, models, _
from odoo.exceptions import UserError


class Postlabel_stock_assignee_user(models.TransientModel):
    _name = 'stock.assignee.user'
    _description = 'Assignee User'

    user_id = fields.Many2one('res.users')
    picking_id = fields.Many2one('stock.picking')

    def process(self):
        self.picking_id.action_assign_user()
        return self.picking_id.action_post_label()
