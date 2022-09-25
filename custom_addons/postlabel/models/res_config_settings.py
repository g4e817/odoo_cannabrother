from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    post_wsdl_url = fields.Char(string="WSDL Url")
    post_client_id = fields.Char(string="Post Client ID")
    post_org_unit_id = fields.Char(string="Post Org Unit ID")
    post_org_unit_guid = fields.Char(string="Post Org Unit GUID")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPsudo = self.env['ir.config_parameter'].sudo()
        post_wsdl_url = ICPsudo.get_param('postlabel.post_wsdl_url')
        post_client_id = ICPsudo.get_param('postlabel.post_client_id')
        post_org_unit_id = ICPsudo.get_param('postlabel.post_org_unit_id')
        post_org_unit_guid = ICPsudo.get_param('postlabel.post_org_unit_guid')
        res.update(
            post_wsdl_url=post_wsdl_url,
            post_client_id=post_client_id,
            post_org_unit_id=post_org_unit_id,
            post_org_unit_guid=post_org_unit_guid

        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('postlabel.post_wsdl_url', self.post_wsdl_url)
        self.env['ir.config_parameter'].set_param('postlabel.post_client_id', self.post_client_id)
        self.env['ir.config_parameter'].set_param('postlabel.post_org_unit_id', self.post_org_unit_id)
        self.env['ir.config_parameter'].set_param('postlabel.post_org_unit_guid', self.post_org_unit_guid)
        return res
