# Copyright (c) 2023, Inventeam Solutions Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
import datetime
import requests
from frappe.model.document import Document
from frappe.integrations.utils import make_get_request

def enqueue_send_whatsapp_message(api_url, contact_number, templatename, keyword, message):
    frappe.enqueue(
        'inventeam_lns.inventeam_lns.doctype.whatsapp_campaign.whatsapp_campaign.send_whatsapp_message',
        queue='short',
        job_name='Whatsapp Notification',
        api_url=api_url,
        contact_number=contact_number,
        templatename=templatename,
        keyword=keyword,
        message=message
    )

@frappe.whitelist()
def send_whatsapp_message(api_url, contact_number, templatename, keyword, message):
    current_datetime = datetime.datetime.now()
    
    response = make_get_request(
            api_url
        )
    
    frappe.msgprint(response, alert=True)
    
    frappe.get_doc({
        "doctype": "Whatsapp Messages",
        "label": templatename,
        "message": message,
        "to": contact_number,
        "keyword": keyword,
        "response": response,
        "sent_time": current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    }).save(ignore_permissions=True)
    
class WhatsappCampaign(Document):
    def after_insert(self):
        wa_setting = frappe.get_doc("Whatsapp Settings", "Whatsapp Settings")
        api_url = wa_setting.api_url
        api_accesstoken = wa_setting.access_token
        api_instanceid = wa_setting.instance_id
        api_message_url = wa_setting.send_message_url
        
        template_name = self.template_name
        wa_template = frappe.get_doc("Whatsapp Templates", template_name)
        wa_message = wa_template.message
        wa_file = wa_template.file
        wa_message_type = wa_template.message_type
        
        api_message_url = api_message_url.replace("{messagetype}", wa_message_type)
        
        if wa_message_type == "media":
            api_message_url = f"{api_message_url}&media_url=https://lns.inventeam.in/{wa_file}&filename=" 
        
        api_message_url = api_message_url.replace("{instanceid}", api_instanceid)
        api_message_url = api_message_url.replace("{accesstoken}", api_accesstoken)
        
        sql_query = """
            SELECT Distinct `tabWhatsapp Contacts`.`mobileno`,`tabWhatsapp Contacts`.`contact_name` FROM `tabWhatsapp Contacts`
            INNER JOIN `tabWhatsapp Contacts Keywords` ON `tabWhatsapp Contacts`.`name` = `tabWhatsapp Contacts Keywords`.`parent`
            WHERE `tabWhatsapp Contacts Keywords`.`keyword`='""" + self.keywords + """';"""
            
        data = frappe.db.sql(sql_query, as_dict=True)
        
        i = 0
        for row in data:
            full_message = wa_message.replace("{$}", row.contact_name)
            new_api_message_url = api_message_url
            new_api_message_url = new_api_message_url.replace("{wamobileno}", "91" + row.mobileno)
            new_api_message_url = new_api_message_url.replace("{wamessage}", full_message)
            new_url = api_url + new_api_message_url
            enqueue_send_whatsapp_message(
                new_url,
                row.mobileno,
                template_name,
                self.keywords,
                full_message
            )
            i += 1
            
        self.message_count = i
        self.save()