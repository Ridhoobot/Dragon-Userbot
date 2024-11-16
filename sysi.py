from datetime import datetime

import psutil
from psutil._common import bytes2human

from Kanger import *

async def generate_sysinfo(workdir):
    #user total
    
    # uptime
    info = {
        'BOOT': (datetime.fromtimestamp(psutil.boot_time())
                 .strftime("%Y-%m-%d %H:%M:%S"))
    }
    # CPU
    cpu_freq = psutil.cpu_freq().current
    if cpu_freq >= 1000:
        cpu_freq = f"{round(cpu_freq / 1000, 2)}GHz"
    else:
        cpu_freq = f"{round(cpu_freq, 2)}MHz"
    info['CPU'] = (
        f"{psutil.cpu_percent(interval=1)}% "
        f"({psutil.cpu_count()}) "
        f"{cpu_freq}"
    )
    # Memory
    vm = psutil.virtual_memory()
    sm = psutil.swap_memory()
    info['RAM'] = (f"{bytes2human(vm.used)}, "
                   f"/ {bytes2human(vm.total)}")
    info['SWAP'] = f"{bytes2human(sm.total)}, {sm.percent}%"
    # Disks
    du = psutil.disk_usage(workdir)
    dio = psutil.disk_io_counters()
    info['DISK'] = (f"{bytes2human(du.used)} / {bytes2human(du.total)} "
                    f"({du.percent}%)")
    if dio:
        info['DISK I/O'] = f"R {bytes2human(dio.read_bytes)} | W {bytes2human(dio.write_bytes)}"
    # Network
    nio = psutil.net_io_counters()
    info['NET I/O'] = f"TX {bytes2human(nio.bytes_sent)} | RX {bytes2human(nio.bytes_recv)}"
    # Sensors
    sensors_temperatures = psutil.sensors_temperatures()
    if sensors_temperatures:
        temperatures_list = [
            x.current
            for x in sensors_temperatures['coretemp']
        ]
        temperatures = sum(temperatures_list) / len(temperatures_list)
        info['TEMP'] = f"{temperatures}\u00b0C"
    info = {f"{key}:": value for (key, value) in info.items()}
    max_len = max(len(x) for x in info)
    return ("<code>\n"
            + "\n".join([f"{x:<{max_len}} {y}" for x, y in info.items()])
            + "</code>")


async def the_sysinfo(client, message):
    response = await generate_sysinfo(client.workdir)
    anu = await get_userbots() 
    await message.reply(f"<b>Kanger#</b> <code>stats total {len(anu)} user</code>\n" + response, quote=True)

async def server_neofetch(client, callback_query):
    await callback_query.message.edit("Processing...")
    lhoini = await generate_sysinfo(client.workdir)
    buttons = [
        [
            InlineKeyboardButton("Back", callback_data="mboh"),
            ],
            ]
    await callback_query.message.edit(
        f"{lhoini}",
        reply_markup=InlineKeyboardMarkup(buttons)
        )