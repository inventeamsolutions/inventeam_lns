# Copyright (c) 2023, Inventeam Solutions Pvt Ltd and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe import _

def get_columns(filters):
    # Define your columns here
    columns = [
        {
            'fieldname': 'message_date',
            'label': _('Message Date'),
            'fieldtype': 'Data',
        },
        {
            'fieldname': 'message',
            'label': _('Message'),
            'fieldtype': 'Data',
        },
        {
            'fieldname': 'message_count',
            'label': _('Message Count'),
            'fieldtype': 'Int',
        },
    ]
    return columns
    
def execute(filters=None):
    f_from_date = filters.get("from_date")
    f_to_date = filters.get("to_date")
    
    columns = get_columns(filters)
    
    query = """SELECT DATE_FORMAT(Sent_Time, '%d %M %Y') AS message_date, label as message, COUNT(NAME) as message_count 
                FROM `tabWhatsapp Messages` Where label <> ''""";

    if f_from_date:
        query = query + """ And Sent_Time>='""" + f_from_date + """'""";
    if f_to_date:
        query = query + """ And Sent_Time<='""" + f_to_date + """'""";

    query = query + """ GROUP BY message_date, label""";
    query = query + """ ORDER BY Sent_Time""";
    
    sql_data = frappe.db.sql(query, as_dict=True)
    
    data = columns, sql_data, None, None, None
    return data
