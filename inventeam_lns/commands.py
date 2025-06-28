import frappe
import click
from inventeam_lns.inventeam_lns.doctype.whatsapp_campaign.whatsapp_campaign import get_single_whatsapp_contact

@click.command('run-30-second-job')
def run_30_second_job():
    get_single_whatsapp_contact()