frappe.ui.form.on('Whatsapp Campaign', {
	refresh: function(frm) {
		frm.set_df_property("whatsapp_campaign_items", "cannot_add_rows", true);
        frm.set_df_property("whatsapp_campaign_items", "cannot_delete_rows", true);

		if(frm.doc.keywords && (frm.doc.whatsapp_campaign_items.length === 0 || !frm.doc.whatsapp_campaign_items)) {
			get_contacts(frm);
		}
	},
	keywords: function(frm) {
		get_contacts(frm);
	}
});

function get_contacts(frm) {
	if(frm.doc.keywords) {
		frappe.call({
			method: "inventeam_lns.inventeam_lns.doctype.whatsapp_campaign.whatsapp_campaign.get_whatsapp_contacts",
			async: false,
			args: {
				'keyword': frm.doc.keywords
			},
			callback: function(response) {
				if(response.message) {
					frm.clear_table('whatsapp_campaign_items');
					response.message.forEach(function(row) {
						var child = frm.add_child('whatsapp_campaign_items');

						child.contact_name = row.contact_name;
						child.mobileno = row.mobileno;
					});
					frm.refresh_field('whatsapp_campaign_items');
				}
			},
		});
	} else {
		frm.clear_table('whatsapp_campaign_items');
		frm.refresh_field('whatsapp_campaign_items');
	}
}