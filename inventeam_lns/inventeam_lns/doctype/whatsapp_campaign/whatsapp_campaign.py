# Copyright (c) 2023, Inventeam Solutions Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
import json
import datetime
import requests
from frappe.model.document import Document
from frappe.integrations.utils import make_post_request

def enqueue_send_whatsapp_message(api_url, wadata, contact_number, templatename, keyword):
    frappe.enqueue(
        'inventeam_lns.inventeam_lns.doctype.whatsapp_campaign.whatsapp_campaign.send_whatsapp_message',
        queue='short',
        job_name='Whatsapp Notification',
        api_url=api_url,
        wadata = wadata,
        contact_number=contact_number,
        templatename=templatename,
        keyword=keyword
    )

@frappe.whitelist()
def send_whatsapp_message(api_url, wadata, contact_number, templatename, keyword):
    current_datetime = datetime.datetime.now()
    
    headers = {
        "content-type": "application/json"
    }
    response = make_post_request(
        api_url,
        headers=headers,
        data=json.dumps(wadata)
    )
    frappe.msgprint(response, alert=True)
    
    frappe.get_doc({
        "doctype": "Whatsapp Messages",
        "label": templatename,
        "message": json.dumps(wadata),
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
        
        new_api_message_url = api_url + api_message_url
        #api_message_url = api_message_url.replace("{messagetype}", wa_message_type)
        
        #if wa_message_type == "media":
        #    api_message_url = f"{api_message_url}&media_url=https://lns.inventeam.in/{wa_file}&filename=" 
        
        #api_message_url = api_message_url.replace("{instanceid}", api_instanceid)
        #api_message_url = api_message_url.replace("{accesstoken}", api_accesstoken)
        
        sql_query = """
            SELECT Distinct `tabWhatsapp Contacts`.`mobileno`,`tabWhatsapp Contacts`.`contact_name` FROM `tabWhatsapp Contacts`
            INNER JOIN `tabWhatsapp Contacts Keywords` ON `tabWhatsapp Contacts`.`name` = `tabWhatsapp Contacts Keywords`.`parent`
            WHERE `tabWhatsapp Contacts Keywords`.`keyword`='""" + self.keywords + """';"""
            
        data = frappe.db.sql(sql_query, as_dict=True)
        
        i = 0
        wadata = {}
        for row in data:
            if wa_message_type == "media":
                wadata = {
                    "number": "91" + row.mobileno,
                    "type": "media",
                    "media_url": "https://lns.inventeam.in/" + wa_file,
                    "message": wa_message.replace("{$}", row.contact_name),
                    "instance_id": api_instanceid,
                    "access_token": api_accesstoken
                }
            else:
                wadata = {
                    "number": "91" + row.mobileno,
                    "type": "media",
                    "media_url": "https://lns.inventeam.in/" + wa_file,
                    "message": wa_message.replace("{$}", row.contact_name),
                    "instance_id": api_instanceid,
                    "access_token": api_accesstoken
                }
                
            #full_message = wa_message.replace("{$}", row.contact_name)
            #new_api_message_url = api_message_url
            #new_api_message_url = new_api_message_url.replace("{wamobileno}", "91" + row.mobileno)
            #new_api_message_url = new_api_message_url.replace("{wamessage}", full_message)
            #new_url = api_url + new_api_message_url
            enqueue_send_whatsapp_message(
                new_api_message_url,
                wadata,
                row.mobileno,
                template_name,
                self.keywords
            )
            i += 1
            
        self.message_count = i
        self.save()