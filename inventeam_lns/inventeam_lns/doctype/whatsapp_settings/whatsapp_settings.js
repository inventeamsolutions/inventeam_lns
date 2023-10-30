// Copyright (c) 2023, Inventeam Solutions Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Whatsapp Settings', {
	refresh: function (frm) {
        frm.add_custom_button('Generate New QR', function () {
            // Call a function to display the image
			frappe.call({
				method: 'inventeam_lns.inventeam_lns.doctype.whatsapp_settings.whatsapp_settings.getqr',
				args: {
					"apiurl": frm.doc.api_url,
					"newinstanceurl": frm.doc.create_instance,
					"newqrcodeurl": frm.doc.get_qr_code,
					"access_token": frm.doc.access_token
				},
				callback: function(response) {
					if (response.message) {
						//frappe.msgprint(response.base64, 'Success', 'green');
						//frappe.msgprint(response.base64, 'Success', 'green');
						showImage(response.message.base64);
					}
				}
			});
        });
    }
});

function showImage(qrstring) {
    var imageHtml = '<img src="'+qrstring+'" />';
    var msgprint = frappe.msgprint(imageHtml, 'Image Viewer');
	
	setTimeout(function() {
        msgprint.hide();
    }, 5000);
}

