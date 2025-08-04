frappe.pages['video-player'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Video Player',
		single_column: true
	});
}