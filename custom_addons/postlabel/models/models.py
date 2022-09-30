# -*- coding: utf-8 -*-
import base64

from odoo import _, models, fields, api, tools
from .service import ZeepWebServiceClient
# from ...queue_job.exception import FailedJobError
# from ...queue_job.job import job, Job, STATES, DONE, FAILED
from odoo.exceptions import except_orm
import threading


class Postlabel_collo_codes(models.Model):
    _name = 'stock.picking.collo'
    _description = 'Collo codes'

    code = fields.Char(string='Collo code')
    number_type = fields.Integer(string="Number Type id")
    ou_carrier_third_party = fields.Char(string='Carrier id')
    post_label_id = fields.Many2one('stock.picking', string='Post Label', ondelete='cascade', readonly=True)


class Postlabel_post_label(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'
    _lock = threading.RLock()
    # post_label = fields.Binary(string="Post label pdf")
    # shipping_document = fields.Binary(string="Shipping document pdf")
    collo_codes = fields.One2many('stock.picking.collo', 'post_label_id')
    assignee_status = fields.Selection(compute='_compute_work', string='Benutzerstatus', default='open', store=True,
                                       selection=[('open', 'Wartend'), ('in_work', 'in Arbeit'),
                                                  ('order_packed', 'Erledigt')])
    assignee_user = fields.Many2one('res.users', 'Zugewiesen')
    # shipper_code = fields.Char(string="Tracking code")
    current_user = fields.Char(string='Auftragstatus', compute='_current_user')
    queue_job_id = fields.Many2one("queue.job", 'Job')
    # job_status = fields.Selection(STATES, compute="_compute_queue_job_status", string="Job Status", readonly=True)
    shipper_url = fields.Char(string="Tracking Url")
    has_post_label = fields.Boolean(string="Has post label")

    # @api.depends('queue_job_id', 'queue_job_id.state')
    # def _compute_queue_job_status(self):
    #    for stock in self:
    #        if stock.queue_job_id:
    #            stock.job_status = _(stock.queue_job_id.state)
    #        else:
    #            stock.job_status = None
    #        #else:
    #        #    stock.job_status = None

    def _check_environment_is_production(self):
        web_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        localhost_names = ['odoo.dr-neuburger.at']
        return True if not web_base_url or any(x in web_base_url for x in localhost_names) else False

    @api.depends('assignee_user', 'assignee_status')
    def _current_user(self):
        for stock in self:
            if stock.assignee_status == 'order_packed':
                stock.current_user = 'verpackt'
            elif stock.assignee_user:
                stock.current_user = stock.assignee_user.name + ' zugewiesen'
            else:
                stock.current_user = 'nicht zugewiesen'

    @api.depends('state', 'assignee_status')
    def _compute_work(self):
        for stock in self:
            if stock.state == 'done':
                stock.assignee_status = 'order_packed'
            elif stock.state == 'cancel':
                stock.assignee_status = 'open'
            elif stock.state == 'assigned' and stock.assignee_user:
                stock.assignee_status = 'in_work'

            if not stock.assignee_status:
                stock.assignee_status = 'open'

    def createAttachment(self, name, data):
        attachment = self.env['ir.attachment'].create({
            'name': name,
            'type': 'binary',
            'datas': data,
            'res_model': 'stock.picking',
            'res_id': self.id,
            'mimetype': 'application/x-pdf'
        })
        return attachment.id

    def createColloCode(self, colloCodes):
        for colloCode in colloCodes:
            self.env['stock.picking.collo'].create(colloCode)

    # @job
    def label_generation(self):
        self.ensure_one()
        client = ZeepWebServiceClient(self.env)
        company_id = self.company_id.partner_id
        if not company_id:
            company_id = self.env.user.company_id.partner_id
        oURecipientAddress = client.createOURecepientAddressWithResPartner(self.partner_id)
        oUShipperAddress = client.createOUShipperAddressAddressWithResPartner(company_id)
        resObj = client.importShipment(oUShipperAddress, oURecipientAddress, self.move_ids_without_package)
        if not resObj.isErrorMessage():
            attachments = []

            post_label = resObj.getPdfData()

            if post_label:
                name_post_label = 'post_label_' + self.partner_id.name + '.pdf'
                attachments.append(self.createAttachment(name_post_label, post_label))

            shipping_document = resObj.getShipmentsDocument()

            if shipping_document:
                name_shipping_document = 'shipping_document_' + self.partner_id.name + '.pdf'
                attachments.append(self.createAttachment(name_shipping_document, shipping_document))

            if attachments:
                self.message_post(attachment_ids=attachments)
                self.has_post_label = True
                self.shipper_url = resObj.getTrackingUrl()  #
                self.createColloCode(resObj.getCode(self.id))
                # self.action_print_post_label(post_label, shipping_document)
            return

        raise except_orm("Fehler!", resObj.getErrorMessage())

        # return

        # raise FailedJobError(resObj.getErrorMessage())

    def action_post_label(self):
        # labelJob = self.with_delay().label_generation()
        # queueJob = Job.db_record_from_uuid(self.env, labelJob.uuid)
        # self.queue_job_id = queueJob

        with self._lock:
            if not self.has_post_label:
                self.label_generation()

    def send_tracking_email(self):
        self.ensure_one()
        stock = self
        # TODO Anhang fehlt und Message
        ctx = {
            'default_model': 'stock.picking',
            'default_res_id': stock.id,
            'default_use_template': True,
            'default_template_id': self.env.ref('postlabel.tracking_code_email_template'),
            'web_base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            'force_email': True,
            'auto_delete': False,
            'partner_id': stock.partner_id,
            'tracking_url': stock.shipper_url,
            'product_ids': stock.move_ids_without_package,
        }
        template = self.env.ref('postlabel.tracking_code_email_template')
        sale_order = self.env['sale.order']
        order = sale_order.search([('picking_ids', 'in', [stock.id])], limit=1)
        if not order:
            raise except_orm("Fehler!", "Es wurde kein zugehöriger Auftrag gefunden.")
        elif not order.invoice_count > 0:
            raise except_orm("Fehler!", "Es wurde noch keine Rechnung für den Auftrag {} erstellt.".format(order.name))
        elif order.invoice_count > 1:
            raise except_orm("Fehler!", "Der Auftrag {} besitzt mehr als eine Rechnung.".format(order.name))

        partner_id = order.partner_id

        if not partner_id.email or partner_id.email == '':
            raise except_orm("Fehler!", "Der Kunde {} hat leider keine E-Mail.".format(partner_id.name))

        invoice = order.invoice_ids[0]
        pdf = self.env.ref('account.account_invoices_without_payment').with_context(
            must_skip_send_to_printer=True
        )._render_qweb_pdf([invoice.id])
        b64_pdf = base64.b64encode(pdf[0])
        ATTACHMENT_NAME = 'Rechnung-{}.pdf'.format(invoice.name)
        attachment = self.env['ir.attachment'].create({
            'name': ATTACHMENT_NAME,
            'type': 'binary',
            'datas': b64_pdf,
            'store_fname': ATTACHMENT_NAME,
            'mimetype': 'application/x-pdf'
        })
        email_values = {
            'recipient_ids': [(6, 0, [partner_id.id])],
            'auto_delete': False
        }
        template.attachment_ids = [(6, 0, [attachment.id])]
        template.with_context(ctx).send_mail(stock.id, email_values=email_values)

    def action_done(self):
        self.send_tracking_email()
        return True
    def _send_confirmation_email(self):
        pass

    def button_validate(self):
        self.ensure_one()
        if not self.has_post_label and not self.carrier_id.product_id.default_code in [
            'will_collect'] and self.picking_type_code != 'incoming':
            view = self.env.ref('postlabel.view_assignee_post_label')
            wiz = self.env['stock.assignee.user'].create({'user_id': self._uid, 'picking_id': self.id})
            return {
                'name': 'Label generieren?',  # TODO missing translation as well in form view
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.assignee.user',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        ret = super(Postlabel_post_label, self).button_validate()
        if ret is True and self.carrier_id.product_id.default_code != 'will_collect':
            self.send_tracking_email()
        return ret
    def delete_attachment_messages(self):
        attachments = self.env['ir.attachment'].search(
            [('res_id', '=', self.id)])

        attachIds = []
        for attach in attachments:
            attachIds.append(attach.id)

        if attachIds:
            messages = self.env['mail.message'].search([('attachment_ids', 'in', attachIds)])
            if messages:
                messages.unlink()
            attachments.unlink()

    # @job
    def remove_post_label(self):
        self.ensure_one()
        client = ZeepWebServiceClient(self.env)
        if self.has_post_label and self.collo_codes:
            codes = []

            for colloCodes in self.collo_codes:
                codes.append(colloCodes.code)

            response = client.cancelShipments(codes)[0]
            if response.CancelSuccessful:  # or response.ErrorCode == 'SN#10020':
                # someone deleted is from post server ( Error Code )
                self.has_post_label = False
                self.shipper_url = None
                self.collo_codes = None
                msg = "Shipment has been successfully removed from the post server!"
                self.delete_attachment_messages()
                self.message_post(body=msg)
                return {'type': 'ir.actions.client', 'tag': 'reload', }

            raise except_orm("Fehler!", response.ErrorMessage)

    def action_cancel_shipment(self):
        # removeLabelJob = self.with_delay().remove_post_label()
        # queueJob = Job.db_record_from_uuid(self.env, removeLabelJob.uuid)
        # self.queue_job_id = queueJob
        return self.remove_post_label()

    def action_assign_user(self):

        self.assignee_user = self._uid
        self.state = 'assigned'

        msg = "Delivery has been assigned to user %s" % self.assignee_user.name
        self.message_post(body=msg)

        # self.action_post_label()

        return True

    def get_post_label_attachment(self):
        names = []
        names.append('post_label_' + self.partner_id.name + '.pdf')
        # names.append('shipping_document_' + self.partner_id.name + '.pdf')

        attachments = self.env['ir.attachment'].search([('name', 'in', names), ('res_id', '=', self.id)], limit=1)

        return attachments

    def get_shipping_attachment(self):
        names = []
        # names.append('post_label_' + self.partner_id.name + '.pdf')
        names.append('shipping_document_' + self.partner_id.name + '.pdf')

        attachment = self.env['ir.attachment'].search([('name', 'in', names), ('res_id', '=', self.id)], limit=1)
        return attachment

    def get_label_printer(self):
        return self.env['printing.printer'].search([('system_name', '=', 'DYMO-Drucker')], limit=1)

    def get_normal_printer(self):
        return self.env['printing.printer'].search([('system_name', '=', 'Ricoh-Drucker')], limit=1)

    def action_print_post_label(self, post_label=None, shipping_document=None):
        attachment = self.get_post_label_attachment()

        if post_label:
            attachment = post_label
        elif attachment:
            attachment = attachment.datas

        if attachment:
            printer = self.get_label_printer()
            if printer:
                report = self.env["ir.actions.report"].search([], limit=1)
                fileData = base64.b64decode(attachment)
                printer.print_document(report, fileData, doc_format="pdf")

        attachment = self.get_shipping_attachment()

        if shipping_document:
            attachment = shipping_document
        elif attachment:
            attachment = attachment.datas

        if attachment:
            printer = self.get_normal_printer()
            if printer:
                report = self.env["ir.actions.report"].search([], limit=1)
                fileData = base64.b64decode(attachment)
                printer.print_document(report, fileData, doc_format="pdf")
        # else:
        #    raise except_orm("Fehler!", "Bitte überprüfe deine Druckereinstellungen in Odoo.")


class EoriNrResCompany(models.Model):
    _inherit = "res.partner"

    eori_nr = fields.Char("EORI Nummer")


class PerformEndOfDay(models.Model):
    _name = "stock.perform.end.of.day"
    _description = "Tagesabschlüsse"
    _order = "creation_date DESC, name DESC"
    pdf_file = fields.Binary(string='Tagesabschluss', attachment=True)
    name = fields.Char(string='Nummer')

    creation_date = fields.Date(string="Erstellungsdatum")

    file_name = fields.Char('Dateiname', default="Tagesabschluss.pdf")


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def fixed_send_shipping(self, pickings):
        res = []
        for p in pickings:
            res = res + [{'exact_price': p.carrier_id.fixed_price,
                          'tracking_number': p.shipper_url}]
        return res

    def fixed_get_tracking_link(self, picking):
        return picking.shipper_url
