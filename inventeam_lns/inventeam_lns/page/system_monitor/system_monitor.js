frappe.pages['system_monitor'].on_page_load = function (wrapper) {
    new MyPage(wrapper);
}

// PAGE CONTENT
MyPage = Class.extend({
    init: function (wrapper) {
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: 'System Monitor',
            single_column: true
        });
        // make page
        frappe.require('/assets/inventeam_lns/js/loader.js', () => {
            this.make();
        })
    },

    // make page
    make: function () {
        // grab the class
        let me = $(this);
        // push dom elemt to page

        // execute methods
        $(frappe.render_template(`
				<div style="text-align:center;">
				<div class="row">
					<div class="col-md-6"id="chart_div" style="width: 100%; height: 400pxpx;"></div>
					<div class="col-md-6"style="width: 100%;" id="desc_table"></div>
				</div>
			 <div id="cpu_frequency_div" style="width: 100%; height: 500px;"></div>
             <div id="network_div" style="width: 100%; height: 300px; margin-top: 20px;"></div>
			 </div>`, this)).appendTo(this.page.main);
        chart_data();

    }// end of class
})


let chart_data = () => {
    setTimeout(() => {
        get_chart_data();
        chart_data();
    }, 3000)
}


let get_chart_data = () => {
    frappe.call({
        method: "inventeam_lns.inventeam_lns.page.system_monitor\
				.system_monitor.execute", //dotted path to server method
        callback: function (r) {
            // code snippet
            data = r.message
            console.log(r);
            document.querySelector('#desc_table').innerHTML = data.desctable;
            render_guage(data);
            render_frequency(data.cpu);
            render_bandwidth(data.network);
        }
    })
}

let render_guage = (r) => {
    google.charts.load('current', { 'packages': ['gauge'] });
    google.charts.setOnLoadCallback(drawChart);

    function drawChart() {

        var data = google.visualization.arrayToDataTable([
            ['Label', 'Value'],
            ['RAM', r.memory.percent],
            ['CPU', r.cpu.percent],
            ['Disk', r.disk.percent]
        ]);

        var options = {
            width: '100%', height: 200,
            redFrom: 90, redTo: 100,
            yellowFrom: 75, yellowTo: 90,
            minorTicks: 5
        };

        var chart = new google.visualization.Gauge(document.getElementById('chart_div'));

        chart.draw(data, options);


        data.setValue(0, 1, r.memory.percent);
        chart.draw(data, options);

        data.setValue(1, 1, r.cpu.percent);
        chart.draw(data, options);

        data.setValue(2, 1, r.disk.percent);
        chart.draw(data, options);
    }
}

// RENDER CPU Frequency

let render_frequency = (r) => {
    google.charts.load('current', { 'packages': ['corechart'] });
    google.charts.setOnLoadCallback(drawChart);
    function drawChart() {
        var data = google.visualization.arrayToDataTable(
            r.cpu_freq_list
        );

        var options = {
            title: `CPU Frequency: max(${r.cpu_max})`,
            hAxis: { title: 'CPU', titleTextStyle: { color: '#333' } },
            vAxis: { minValue: 0, maxValue: r.cpu_max }
        };

        var chart = new google.visualization.AreaChart(document.getElementById('cpu_frequency_div'));
        chart.draw(data, options);
    }
}

let render_bandwidth = (net) => {
    google.charts.load('current', { packages: ['corechart'] });
    google.charts.setOnLoadCallback(drawChart);

    if (!window.networkData) {
        window.networkData = [['Time', 'Upload (KB/s)', 'Download (KB/s)']];
    }

    let currentTime = new Date().toLocaleTimeString();
    window.networkData.push([currentTime, net.sent_kbps, net.recv_kbps]);

    // keep only last 20 samples
    if (window.networkData.length > 20) {
        window.networkData.splice(1, 1);
    }

    function drawChart() {
        var data = google.visualization.arrayToDataTable(window.networkData);
        var options = {
            title: 'Network Bandwidth (KB/s)',
            curveType: 'function',
            legend: { position: 'bottom' },
            hAxis: { textStyle: { fontSize: 10 } },
            vAxis: { minValue: 0 }
        };

        var chart = new google.visualization.LineChart(document.getElementById('network_div'));
        chart.draw(data, options);
    }
}
