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
    # Send Message between 9 A.M. to 8 P.M
    from frappe.utils import now_datetime

    current_time = now_datetime().time()

    # Define your time window
    from datetime import time as dt_time
    start_time = dt_time(9, 0, 0)   # 9:00 AM
    end_time = dt_time(20, 0, 0)    # 8:00 PM

    if not (start_time <= current_time <= end_time):
        frappe.logger().info("WhatsApp sending skipped: Outside working hours.")
        return

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
        ORDER BY wci.creation ASC LIMIT 2
    """
    sql_data = frappe.db.sql(sql_query, as_dict=True)

    wadata = {}
    if sql_data:
        for row in sql_data:
        #row = sql_data[0]

            template_name = row.template_name
            wa_template = frappe.get_doc("Whatsapp Templates", template_name)
            wa_message = wa_template.message
            wa_file = wa_template.file
            wa_message_type = wa_template.message_type

            if wa_message_type == "media":
                wadata = {
                    "number": "91" + row.mobileno,
                    "type": "media",
                    "media_url": "https://" + current_domain + wa_file,
                    "message": wa_message.replace("{$}", row.contact_name),
                    "instance_id": api_instanceid,
                    "access_token": api_accesstoken
                }
            else:
                wadata = {
                    "number": "91" + row.mobileno,
                    "type": "text",
                    "message": wa_message.replace("{$}", row.contact_name),
                    "instance_id": api_instanceid,
                    "access_token": api_accesstoken
                }

            enqueue_send_whatsapp_message(
                new_api_message_url,
                wadata,
                row.mobileno,
                template_name,
                row.keywords
            )
            frappe.db.set_value("Whatsapp Campaign Items", row.name, "sent", 1)

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

def enqueue_send_whatsapp_message_meta(api_url,authorization_code, wadata, contact_number, templatename, keyword):

    frappe.enqueue(
        'inventeam_lns.inventeam_lns.doctype.whatsapp_campaign.whatsapp_campaign.send_whatsapp_message_meta',
        queue='short',
        job_name='Whatsapp Notification',
        api_url=api_url,
        authorization_code = authorization_code,
        wadata = wadata,
        contact_number=contact_number,
        templatename=templatename,
        keyword=keyword
    )

@frappe.whitelist()
def send_whatsapp_message_meta(api_url, authorization_code, wadata, contact_number, templatename, keyword):
    current_datetime = datetime.datetime.now()

    headers = {
        "content-type": "application/json",
        "Authorization": authorization_code
    }
    response = make_post_request(
        api_url,
        headers=headers,
        data=json.dumps(wadata)
    )
    #frappe.msgprint(response, alert=True)

    frappe.get_doc({
        "doctype": "Whatsapp Messages",
        "label": templatename,
        "to": contact_number,
        "keyword": keyword,
        "request_data": wadata,
        "response_data": response,
        "sent_time": current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    }).save(ignore_permissions=True)

class WhatsappCampaign(Document):
    def after_insert(self):
        wa_setting = frappe.get_doc("Whatsapp Settings", "Whatsapp Settings")
        api_url = wa_setting.api_url
        api_accesstoken = wa_setting.access_token
        api_instanceid = wa_setting.instance_id
        api_message_url = wa_setting.send_message_url

        meta_api_url = wa_setting.meta_api_url
        meta_authorization_code = wa_setting.meta_authorization_code
        document_template = wa_setting.document_template
        image_template = wa_setting.image_template
        video_template = wa_setting.video_template
        file_name = wa_setting.file_name


        template_name = self.template_name
        wa_template = frappe.get_doc("Whatsapp Templates", template_name)
        wa_message = wa_template.message
        wa_file = wa_template.file
        wa_message_type = wa_template.message_type

        new_api_message_url = api_url + api_message_url

        sql_query = """
            SELECT Distinct `tabWhatsapp Contacts`.`mobileno`,`tabWhatsapp Contacts`.`contact_name` FROM `tabWhatsapp Contacts`
            INNER JOIN `tabWhatsapp Contacts Keywords` ON `tabWhatsapp Contacts`.`name` = `tabWhatsapp Contacts Keywords`.`parent`
            WHERE `tabWhatsapp Contacts Keywords`.`keyword`='""" + self.keywords + """';"""

        data = frappe.db.sql(sql_query, as_dict=True)

        # Get the base URL
        base_url = get_request_site_address()

        # Parse the base URL to extract the domain
        parsed_url = urlparse(base_url)
        current_domain = parsed_url.netloc

        i = 0
        wadata = {}
        for row in data:
            if meta_api_url:
                template_name = ''
                if wa_message_type == "document":
                    template_name = document_template
                elif wa_message_type == "image":
                    template_name = image_template
                elif wa_message_type == "video":
                    template_name = video_template

                wadata = meta_message_body("91" + row.mobileno, template_name, wa_message_type, "https://" + current_domain + wa_file, file_name, wa_message)

                enqueue_send_whatsapp_message_meta(
                    meta_api_url,
                    meta_authorization_code,
                    wadata,
                    row.mobileno,
                    template_name,
                    self.keywords
                )
            else:
                if wa_message_type == "media":
                    wadata = {
                        "number": "91" + row.mobileno,
                        "type": "media",
                        "media_url": "https://" + current_domain + wa_file,
                        "message": wa_message.replace("{$}", row.contact_name),
                        "instance_id": api_instanceid,
                        "access_token": api_accesstoken
                    }
                else:
                    wadata = {
                        "number": "91" + row.mobileno,
                        "type": "text",
                        "message": wa_message.replace("{$}", row.contact_name),
                        "instance_id": api_instanceid,
                        "access_token": api_accesstoken
                    }

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


def meta_message_body(contact_number, templatename, wa_message_type, file_link, file_name, message):
    if wa_message_type == "document":
        wadata = {
                    "to": contact_number,
                    "type": "template",
                    "source": "external",
                    "template": {
                        "name": templatename,
                        "language": {
                        "code": "en"
                        },
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                {
                                    "type": "document",
                                    "document": {
                                        "link": file_link,
                                        "filename": file_name
                                    }
                                }
                                ]
                            },
                            {
                                "type": "body",
                                "parameters": [
                                    {
                                        "type": "text",
                                        "text": message
                                    }
                                ]
                            }
                        ]
                    },
                    "metaData": {
                        "custom_callback_data": "<optional_value>"
                    }
                }
    elif wa_message_type == "image":
       wadata = {
                    "to": contact_number,
                    "type": "template",
                    "source": "external",
                    "template": {
                        "name": templatename,
                        "language": {
                        "code": "en"
                        },
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                {
                                    "type": "image",
                                    "image": {
                                        "link": file_link,
                                        "filename": file_name
                                    }
                                }
                                ]
                            },
                            {
                                "type": "body",
                                "parameters": [
                                    {
                                        "type": "text",
                                        "text": message
                                    }
                                ]
                            }
                        ]
                    },
                    "metaData": {
                        "custom_callback_data": "<optional_value>"
                    }
                }
    elif wa_message_type == "video":
       wadata = {
                    "to": contact_number,
                    "type": "template",
                    "source": "external",
                    "template": {
                        "name": templatename,
                        "language": {
                        "code": "en"
                        },
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                {
                                    "type": "video",
                                    "video": {
                                        "link": file_link
                                    }
                                }
                                ]
                            },
                            {
                                "type": "body",
                                "parameters": [
                                    {
                                        "type": "text",
                                        "text": message
                                    }
                                ]
                            }
                        ]
                    },
                    "metaData": {
                        "custom_callback_data": "<optional_value>"
                    }
                }
    return wadata