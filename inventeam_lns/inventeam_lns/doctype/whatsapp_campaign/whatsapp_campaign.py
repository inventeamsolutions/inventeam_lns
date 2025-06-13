import frappe
import json
import datetime
import requests
from frappe.utils import get_request_site_address
from urllib.parse import urlparse
from frappe.model.document import Document
from frappe.integrations.utils import make_post_request

class WhatsappCampaign(Document):
    def after_insert(self):
        total_count = len(self.get("whatsapp_campaign_items"))
        
        self.message_count = total_count
        self.save()


@frappe.whitelist()
def get_whatsapp_contacts(keyword):
    sql_query = f"""
        SELECT Distinct wc.mobileno, wc.contact_name FROM `tabWhatsapp Contacts` AS wc
        INNER JOIN `tabWhatsapp Contacts Keywords` AS wce ON wc.name = wce.parent
        WHERE wce.keyword='{keyword}'
    """
    sql_data = frappe.db.sql(sql_query, as_dict=True)

    return sql_data


@frappe.whitelist()
def get_single_whatsapp_contact():
    wa_setting = frappe.get_doc("Whatsapp Settings", "Whatsapp Settings")
    api_url = wa_setting.api_url
    api_accesstoken = wa_setting.access_token
    api_instanceid = wa_setting.instance_id
    api_message_url = wa_setting.send_message_url

    new_api_message_url = api_url + api_message_url

    # Get the base URL
    base_url = get_request_site_address()

    # Parse the base URL to extract the domain
    parsed_url = urlparse(base_url)
    current_domain = parsed_url.netloc

    sql_query = f"""
        SELECT wc.template_name, wc.keywords, wc.message_count, wci.contact_name, wci.mobileno, wci.sent, wci.name, wci.parent
        FROM `tabWhatsapp Campaign Items` AS wci
        INNER JOIN `tabWhatsapp Campaign` AS wc
        ON wci.parent=wc.name
        WHERE wci.sent=0
        ORDER BY wci.creation ASC LIMIT 1
    """
    sql_data = frappe.db.sql(sql_query, as_dict=True)

    wadata = {}
    if sql_data:
        row = sql_data[0]
        
        template_name = row["template_name"]
        wa_template = frappe.get_doc("Whatsapp Templates", template_name)
        wa_message = wa_template.message
        wa_file = wa_template.file
        wa_message_type = wa_template.message_type

        if wa_message_type == "media":
            wadata = {
                "number": "91" + row["mobileno"],
                "type": "media",
                "media_url": "https://" + current_domain + wa_file,
                "message": wa_message.replace("{$}", row["contact_name"]),
                "instance_id": api_instanceid,
                "access_token": api_accesstoken
            }
        else:
            wadata = {
                "number": "91" + row["mobileno"],
                "type": "text",
                "message": wa_message.replace("{$}", row["contact_name"]),
                "instance_id": api_instanceid,
                "access_token": api_accesstoken
            }
            
        enqueue_send_whatsapp_message(
            new_api_message_url,
            wadata,
            row["mobileno"],
            template_name,
            row["keywords"]
        )
        frappe.db.set_value("Whatsapp Campaign Items", row["name"], "sent", 1)
        
    
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
        "to": contact_number,
        "keyword": keyword,
        "request_data": wadata,
        "response_data": response,
        "sent_time": current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    }).save(ignore_permissions=True)
    
# class WhatsappCampaign(Document):
#     def after_insert(self):
#         wa_setting = frappe.get_doc("Whatsapp Settings", "Whatsapp Settings")
#         api_url = wa_setting.api_url
#         api_accesstoken = wa_setting.access_token
#         api_instanceid = wa_setting.instance_id
#         api_message_url = wa_setting.send_message_url
        
#         template_name = self.template_name
#         wa_template = frappe.get_doc("Whatsapp Templates", template_name)
#         wa_message = wa_template.message
#         wa_file = wa_template.file
#         wa_message_type = wa_template.message_type
        
#         new_api_message_url = api_url + api_message_url
   
#         sql_query = """
#             SELECT Distinct `tabWhatsapp Contacts`.`mobileno`,`tabWhatsapp Contacts`.`contact_name` FROM `tabWhatsapp Contacts`
#             INNER JOIN `tabWhatsapp Contacts Keywords` ON `tabWhatsapp Contacts`.`name` = `tabWhatsapp Contacts Keywords`.`parent`
#             WHERE `tabWhatsapp Contacts Keywords`.`keyword`='""" + self.keywords + """';"""
            
#         data = frappe.db.sql(sql_query, as_dict=True)
        
#         # Get the base URL
#         base_url = get_request_site_address()

#         # Parse the base URL to extract the domain
#         parsed_url = urlparse(base_url)
#         current_domain = parsed_url.netloc

#         i = 0
#         wadata = {}
#         for row in data:
#             if wa_message_type == "media":
#                 wadata = {
#                     "number": "91" + row.mobileno,
#                     "type": "media",
#                     "media_url": "https://" + current_domain + wa_file,
#                     "message": wa_message.replace("{$}", row.contact_name),
#                     "instance_id": api_instanceid,
#                     "access_token": api_accesstoken
#                 }
#             else:
#                 wadata = {
#                     "number": "91" + row.mobileno,
#                     "type": "text",
#                     "message": wa_message.replace("{$}", row.contact_name),
#                     "instance_id": api_instanceid,
#                     "access_token": api_accesstoken
#                 }
                
#             enqueue_send_whatsapp_message(
#                 new_api_message_url,
#                 wadata,
#                 row.mobileno,
#                 template_name,
#                 self.keywords
#             )
#             i += 1
            
#         self.message_count = i
#         self.save()