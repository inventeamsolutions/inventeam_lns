import frappe, psutil, time, platform, os, datetime


@frappe.whitelist()
def execute(**kwargs):
    res = frappe._dict({})
    if not ('System Manager' in [i.role for i in frappe.get_doc('User', frappe.session.user).roles]):
        return res
    desctable = frappe.render_template(
		"inventeam_lns/inventeam_lns/page/system_monitor/desctable.html",
		context=dict(
            name= platform.system(),
            release= platform.release(),
            running_since=datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),

        ))
    res.desctable = desctable
    cpu = frappe._dict({})
    cpu.percent = psutil.cpu_percent(interval=0)
    initial_cpu = psutil.cpu_freq(percpu=True)
    cpu_max = initial_cpu[0].max
    cpu_freq_list = [['CPU']+[str(i) for i in range(1, len(initial_cpu)+1)]]
    for i in range(1, len(initial_cpu)+1):
        fr = psutil.cpu_freq(percpu=True)
        cpu_freq_list.append(['']+[i.current for i in fr])
        time.sleep(0.4)
    cpu.cpu_freq_list = cpu_freq_list
    cpu.cpu_max = cpu_max

    memory = frappe._dict({})
    disk = frappe._dict({})
    memory.percent = psutil.virtual_memory()[2]
    disk.percent = psutil.disk_usage('/')[3]

    # Network (Bandwidth)
    net1 = psutil.net_io_counters()
    time.sleep(1)
    net2 = psutil.net_io_counters()

    bytes_sent = net2.bytes_sent - net1.bytes_sent
    bytes_recv = net2.bytes_recv - net1.bytes_recv
    res.network = frappe._dict({
        'sent_kbps': round(bytes_sent / 1024, 2),
        'recv_kbps': round(bytes_recv / 1024, 2),
    })

    res.memory = memory
    res.cpu = cpu
    res.disk = disk
    return res


@frappe.whitelist(allow_guest=True)
def server_status(**kwargs):
    res = frappe._dict({})
    res.platform = platform.system()
    res.running_since=datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    cpu = frappe._dict({})
    cpu.percent = psutil.cpu_percent(interval=0)
    initial_cpu = psutil.cpu_freq(percpu=True)
    cpu_max = initial_cpu[0].max
    cpu_freq_list = [['CPU']+[str(i) for i in range(1, len(initial_cpu)+1)]]
    for i in range(1, len(initial_cpu)+1):
        fr = psutil.cpu_freq(percpu=True)
        cpu_freq_list.append(['']+[i.current for i in fr])
        time.sleep(0.4)
    cpu.cpu_freq_list = cpu_freq_list
    cpu.cpu_max = cpu_max

    memory = frappe._dict({})
    disk = frappe._dict({})
    memory.percent = psutil.virtual_memory()[2]
    disk.percent = psutil.disk_usage('/')[3]
    res.memory = memory
    res.cpu = cpu
    res.disk = disk
    return res