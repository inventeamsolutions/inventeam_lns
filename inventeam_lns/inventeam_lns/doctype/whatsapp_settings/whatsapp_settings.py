# Copyright (c) 2023, Inventeam Solutions Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.integrations.utils import make_get_request

@frappe.whitelist()
def getqr(apiurl, newinstanceurl, newqrcodeurl, access_token):
    if access_token:
        response = make_get_request(
                f"{apiurl}{newinstanceurl}{access_token}"
            )
        doc = frappe.get_doc("Whatsapp Settings", "Whatsapp Settings")
        doc.instance_id = response['instance_id']
        doc.save()
        
        qrcodeurl = newqrcodeurl.replace("{instanceid}", response['instance_id']).replace("{accesstoken}", access_token) 
        response_qr = make_get_request(
                f"{apiurl}{qrcodeurl}"
            )
        
    return response_qr

class WhatsappSettings(Document):
	pass
