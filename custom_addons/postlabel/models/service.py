from uuid import UUID
from zeep import Client
import base64
CID_AT = 'AT'


class ZeepWebServiceClient:
    def __init__(self, is_production):

        if is_production:
            self.wsdl = 'https://plc.post.at/Post.Webservice/ShippingService.svc?WSDL'
        else:
            self.wsdl = 'https://abn-plc.post.at/DataService/Post.Webservice/ShippingService.svc?WSDL'


        self.clientId = 21229941
        self.orgUnitId = 58053489
        self.orgUnitGUID = UUID('531588f8-7aaf-4897-aae9-c01c97c2f432')
        self.client = None
        self.country_id = None
        self.initClient()



    def initClient(self):
        self.client = Client(wsdl=self.wsdl)

    def getClient(self):
        return self.client

    def selectProductCode(self):
        if self.country_id == CID_AT:
            return '30'

        return '70'

    def createOURecepientAddress(self, name, city, address, postalcode, countryId):
        client = self.client
        ou_recipient_address_type = client.get_type('ns1:AddressRow')

        ou_recipient_address = ou_recipient_address_type(Name1=name,
                                                         City=city,
                                                         AddressLine1=address,
                                                         PostalCode=postalcode,
                                                         CountryID=countryId)
        return ou_recipient_address

    def createOUShipperAddressAddressWithResPartner(self, res_partner):
        client = self.client
        ou_recipient_address_type = client.get_type('ns1:AddressRow')
        country_id = res_partner.country_id.code
        ou_shipper_address = ou_recipient_address_type(Name1=res_partner.name,
                                                        City=res_partner.city,
                                                        AddressLine1=res_partner.street,
                                                        PostalCode=res_partner.zip,
                                                        CountryID=country_id,
                                                        EORINumber=res_partner.eori_nr,
                                                        Email=res_partner.email,
                                                        Tel1=res_partner.phone)

        return ou_shipper_address

    def createOURecepientAddressWithResPartner(self, res_partner):
        client = self.client
        ou_recipient_address_type = client.get_type('ns1:AddressRow')
        self.country_id = res_partner.country_id.code
        company_name =  res_partner.custom_companyname or res_partner.company_name
        if company_name:
            ou_recipient_address = ou_recipient_address_type(Name1=company_name,
                                                            Name2=res_partner.name,
                                                            City=res_partner.city,
                                                            AddressLine1=res_partner.street,
                                                            PostalCode=res_partner.zip,
                                                            CountryID=self.country_id)
        else:
            ou_recipient_address = ou_recipient_address_type(Name1=res_partner.name,
                                                            City=res_partner.city,
                                                            AddressLine1=res_partner.street,
                                                            PostalCode=res_partner.zip,
                                                            CountryID=self.country_id)

        information_available = False

        if res_partner.email:
            ou_recipient_address.Email = res_partner.email
            information_available = True
        if res_partner.phone:
            ou_recipient_address.Tel1 = res_partner.phone
            information_available = True

        if self.country_id != CID_AT:
            if not information_available:
                # We set this because otherwise the post api tells us that this is missing
                # TODO: Check if this is the correct way to do
                ou_recipient_address.Tel1 = "+43722480574"

        return ou_recipient_address

    def createColloRow(self, moveLine):
        client = self.client
        collo_row_array_type = client.get_type('ns1:ArrayOfColloRow')
        collo_row_array = collo_row_array_type()

        collo_article_row_array_type = client.get_type('ns1:ArrayOfColloArticleRow')
        collo_article_row_array = collo_article_row_array_type()
        for move in moveLine:
            product = move.product_id

            #print("\n")
            #print("ArticleName:", product.name)
            #print("Quantity:", move.product_uom_qty)
            #print("HSTariffNumber:", int(product.hs_code_id.hs_code))
            #print("ValueOfGoodsPerUnit:", product.lst_price)
            #print("ConsumerUnitNetWeight:", product.weight)
            #print("\n")
            
            collo_article_row_type = client.get_type('ns1:ColloArticleRow')
            
            collo_article_row = collo_article_row_type(ArticleName=product.name,
                                                       Quantity=move.product_uom_qty,
                                                       UnitID='PCE',
                                                       HSTariffNumber=int(product.hs_code_id.hs_code),
                                                       CountryOfOriginID='AT',
                                                       ValueOfGoodsPerUnit=product.lst_price,
                                                       CurrencyID='EUR',  # Währung
                                                       ConsumerUnitNetWeight=product.weight,  # Nettogewicht des Artikels
                                                       CustomsOptionID=1)  # Verkauf von Waren
            
            collo_article_row_array['ColloArticleRow'].append(collo_article_row)

        collo_row_type = client.get_type('ns1:ColloRow')
        collo_row = collo_row_type(ColloArticleList=collo_article_row_array)

        collo_row_array['ColloRow'].append(collo_row)
        return collo_row_array

    def createShipmentRow(self, oUShipperAddress, oURecipientAddress, moveLine):
        client = self.client
        shipment_row_type = client.get_type('ns1:ShipmentRow')
        printer_row = self.createPrinterRow()
        shipment_row = shipment_row_type(ClientID=self.clientId,
                                         OrgUnitID=self.orgUnitId,
                                         OrgUnitGuid=self.orgUnitGUID,
                                         DeliveryServiceThirdPartyID=self.selectProductCode(),
                                         OURecipientAddress=oURecipientAddress,
                                         OUShipperAddress=oUShipperAddress,
                                         PrinterObject=printer_row)

        if self.country_id != CID_AT:
            collo_row_array = self.createColloRow(moveLine)
            shipment_row.ColloList = collo_row_array
        return shipment_row

    def createPrinterRow(self):
        client = self.client
        printer_row_type = client.get_type('ns1:PrinterRow')
        printer_row = printer_row_type(LanguageID='PDF',
                                       Encoding='UTF-8',
                                       LabelFormatID='100x150',
                                       PaperLayoutID='100x150')
        return printer_row

    def importShipment(self, oUShipperAddress, oURecipientAddress, moveLine):
        client = self.client
        shipment_row = self.createShipmentRow(oUShipperAddress, oURecipientAddress, moveLine)
        response = client.service.ImportShipment(row=shipment_row)
        #print(response)
        return ImportShipmentResult(response)

    def postPerformEndOfDay(self):
        client = self.client
        #shipment_row = self.createShipmentRow(oURecipientAddress, moveLine)
        response = client.service.PerformEndOfDay(clientID=self.clientId,
                                                orgUnitID=self.orgUnitId,
                                                orgUnitGuid=self.orgUnitGUID)
        #print(response)
        return PerformEndOfDayResult(response)

    def createCancelShipment(self, codes):
        client = self.client
        #codes = ['1019413500065293908400', '1019413500065303908406', 'CG600177208AT', 'CG600177199AT']
        number = codes[0]
        cancel_shipment_row_array_type = client.get_type('ns1:ArrayOfCancelShipmentRow')
        cancel_shipment_row_type = client.get_type('ns1:CancelShipmentRow')
        
        #print('\n\nCOLLO CODES\n\n', codes, '\n')
        
        #for i in range(0, )
        #print("\n", number, codes, self.clientId, self.orgUnitId, self.orgUnitGUID, "\n")
        cancel_shipment_row = cancel_shipment_row_type(ClientID=self.clientId,
                                                       OrgUnitID=self.orgUnitId,
                                                       OrgUnitGuid=self.orgUnitGUID,
                                                       Number=number,
                                                       ColloCodeList=codes)
        cancel_shipment_row_array = cancel_shipment_row_array_type()
        cancel_shipment_row_array['CancelShipmentRow'].append(cancel_shipment_row)
        return cancel_shipment_row_array

    def cancelShipments(self, codes):
        client = self.client
        cancelChipmentObj = self.createCancelShipment(codes)
        return client.service.CancelShipments(shipments=cancelChipmentObj)


class ImportShipmentResult:

    def __init__(self, response):
        self.shipment = response

    def isErrorMessage(self):
        return self.shipment.errorCode or self.shipment.errorMessage

    def getErrorMessage(self):
        return self.shipment.errorMessage

    def getErrorCode(self):
        return self.shipment.errorCode

    def getCode(self, postLabelId=None):
        colloCodes = []
        for row in self.shipment.ImportShipmentResult.ColloRow:
            for code in row.ColloCodeList.ColloCodeRow:
                colloCodes.append({
                    'code': code.Code,
                    'number_type': code.NumberTypeID,
                    'ou_carrier_third_party': code.OUCarrierThirdPartyID,
                    'post_label_id': postLabelId
                })
        return colloCodes

    def getPdfData(self):
        return self.shipment.pdfData

    def getShipmentsDocument(self):
        return self.shipment.shipmentDocuments

    def getTrackingCode(self):
        return self.getCode()[0].get('code')

    def getTrackingUrl(self):
        return 'https://www.post.at/sv/sendungsdetails?snr=' + self.getTrackingCode()


class CancelShipmentsResult:
    def __init__(self, response):
        self.result = response

class PerformEndOfDayResult:
    def __init__(self, response):
        self.result = response

    def getPdfData(self):
        return self.result.PerformEndOfDayResult

    def isErrorMessage(self):
        return self.result.errorCode

    def getErrorMessage(self):
        return self.result.errorMessage


exports = {ZeepWebServiceClient}

__exports__ = exports
