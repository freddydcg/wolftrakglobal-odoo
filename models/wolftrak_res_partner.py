# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
import requests, json
import sys, os
from bs4 import BeautifulSoup
_logger = logging.getLogger(__name__)
from rnc_wolftrak import Rnc

main_base = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_NAME = "config.json"      
CONFIG_FILE = os.path.join(main_base, CONFIG_FILE_NAME)

def load_config(json_file):
    with open(json_file, 'r') as file:
        config_data = json.load(file)
    return config_data
  
def get_rnc_record(rnc, config_data = None):

    if not config_data:
        config_data = load_config(CONFIG_FILE)
    req_headers = config_data['request_headers']
    # req_cookies = config_data.get('request_cookies')
    req_params = config_data['request_parameters']
    uri = ''.join([config_data['url'], config_data['web_resource']])

    req_params['txtRncCed'] = rnc
    result = requests.get(uri, params = req_params, headers=req_headers)
    if result.status_code == requests.codes.ok:
        soup = BeautifulSoup(result.content)
        data_rows  = soup.find('tr', attrs={'class': 'GridItemStyle'})
        try:
            tds = data_rows.findChildren('td')
            rnc_vals = [str(td.text.strip()) for td in tds]
            # rnc = Rnc(rnc_vals)
            return rnc_vals
        except :
            pass


class WolftrakPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    # @api.depends('total_device')
    # def _set_total_devices(self):
    #
    #     partner_invs = self.env['account.invoice'].search([('partner_id','=',self.id)])
    #     _logger.info(self.env.context)
    #     devices = 0
    #     for inv in partner_invs:
    #         for lines in inv.invoice_line_ids:
    #             if lines.product_id.name == 'Dispositivo GPS':
    #                 devices = + 1
    #     # self.total_device = devices
    #     return devices

    def _default_user_id(self):
        return self.env.uid

    doc_ident = fields.Char(string='Documento de Identificación')
    dgii_state = fields.Char(string='Estado')
    pay_reg = fields.Char(string='Regimen de Pago')
    doc_ident_type = fields.Integer(string='Tipo de Documento')
    user_id = fields.Many2one('res.users', string='Comercial', default=_default_user_id)
    total_device = fields.Integer(string='Dispositivos', help='Total de dispositivos vendidos a este cliente.')

    def _get_partner_invoices(self):
        invoices = self.env['account.invoice']
        par_inv = invoices.search([])
        return par_inv

    def _get_invoices(self):
        invoices = self.env['account.invoice']
        par_inv = invoices.search([])
        for partner in self:
            partner.partner_inv += par_inv.search([('partner_id','=',partner.id)])

    partner_inv = fields.Many2many('account.invoice', default=_get_partner_invoices, compute=_get_invoices)

    @api.onchange('doc_ident','phone')
    def user_validation(self):

        if self.doc_ident:
            if len(self.doc_ident) == 11: self.doc_ident_type = 2
            elif len(self.doc_ident) == 9: self.doc_ident_type = 1

        db_doc_ident = self.search([('doc_ident', '=', self.doc_ident)])
        if db_doc_ident and self.doc_ident:
            raise ValidationError(_('Este Cliente ya se encuentra registrado'))
            self.doc_ident = ''
        db_user_client = self.search([('phone','=',self.phone)])
        if db_user_client and self.phone:
            raise  ValidationError(_('Este Cliente ya se encuentra registrado'))
            self.phone = ''
        try:
            rnc_record = get_rnc_record(self.doc_ident)
            self.name = rnc_record[1]
            self.dgii_state = rnc_record[5]
            self.pay_reg = rnc_record[4]
        except :
            pass

    # def device_history(self):
    #     partner_invs = self.env['account.invoice'].search([('partner_id','=',self.id)])
    #     _logger.info(self.env.context)
    #     devices = 0
    #     for inv in partner_invs:
    #         for lines in inv.invoice_line_ids:
    #             if lines.product_id.name == 'Dispositivo GPS':
    #                 devices = + 1
    #
    #     _logger.info("Dispositivos: ")
    #     _logger.info(devices)
    #     return False
