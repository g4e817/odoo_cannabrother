from odoo import fields, models, _
from odoo.exceptions import UserError
from ..models.service import ZeepWebServiceClient
from odoo.exceptions import except_orm

class Postlabel_stock_performendofday(models.TransientModel):
    _name = 'stock.picking.performendofday'
    _description = 'Tagesabschluss'
    
    name = fields.Char("Bezeichnung")

    def _check_environment_is_production(self):
        web_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        localhost_names = ['odoo.dr-neuburger.at']
        return True if not web_base_url or any(x in web_base_url for x in localhost_names) else False

    def perform_end_of_day(self):
        client = ZeepWebServiceClient(self.env)
        resObj = client.postPerformEndOfDay()
        base64pdf = False
        if not resObj.isErrorMessage():
            base64pdf = resObj.getPdfData()
        else:
            raise except_orm("Fehler!", resObj.getErrorMessage())
            
        return base64pdf


    def process(self):
        base64pdf = self.perform_end_of_day()
        if base64pdf:
            count = self.env['stock.perform.end.of.day'].search_count([]) + 1
            performendofday_vals = {
                'pdf_file': base64pdf,
                'name': self.name if self.name else 'Tagesabschluss ' + str(count),
                'creation_date': fields.Date.today()
    
            }

            self.env['stock.perform.end.of.day'].create(performendofday_vals)
            

        
        #print("\n\nTEST PROCESS: " + self.picking_id.name)
        #print("\n\n")
        #return False
