import json
import os
import platform
import subprocess
import time


class MissionComputer:
    def __init__(self, setting_file='setting.txt'):
        self.setting_file = setting_file

    def _load_settings(self):
        settings = {
            'info': [
                'operating_system',
                'operating_system_version',
                'cpu_type',
                'cpu_core_count',
                'memory_size'
            ],
            'load': [
                'cpu_usage',
                'memory_usage'
            ]
        }

        try:
            if not os.path.exists(self.setting_file):
                return settings

            with open(self.setting_file, 'r', encoding='utf-8') as file:
                for raw_line in file:
                    line = raw_line.strip()

                    if not line:
                        continue

                    if line.startswith('#'):
                        continue

                    if '=' not in line:
                        continue

                    key, value = line.split('=', 1)
                    key = key.strip().lower()
                    items = []

                    for item in value.split(','):
                        item = item.strip()
                        if item:
                            items.append(item)

                    if key == 'info' and items:
                        settings['info'] = items
                    elif key == 'load' and items:
                        settings['load'] = items

        except OSError:
            pass

        return settings

    def _select_items(self, data, keys):
        if 'error' in data:
            return data

        selected = {}

        for key in keys:
            if key in data:
                selected[key] = data[key]

        return selected

    def _run_command(self, command):
        output = subprocess.check_output(
            command,
            stderr=subprocess.STDOUT
        )
        return output.decode('utf-8', errors='ignore').strip()

    def _format_size(self, size_bytes):
        if size_bytes is None:
            return 'Unavailable'

        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        index = 0

        while size >= 1024 and index < len(units) - 1:
            size /= 1024
            index += 1

        return '{:.2f} {}'.format(size, units[index])

    def _get_cpu_type(self):
        system_name = platform.system()

        try:
            if system_name == 'Linux':
                with open('/proc/cpuinfo', 'r', encoding='utf-8') as file:
                    for line in file:
                        if line.lower().startswith('model name'):
                            return line.split(':', 1)[1].strip()

            if system_name == 'Darwin':
                return self._run_command(
                    ['sysctl', '-n', 'machdep.cpu.brand_string']
                )

            if system_name == 'Windows':
                return self._run_command([
                    'powershell',
                    '-Command',
                    '(Get-CimInstance Win32_Processor).Name'
                ])

        except (OSError, subprocess.SubprocessError, FileNotFoundError):
            pass

        cpu_name = platform.processor()
        if cpu_name:
            return cpu_name

        return platform.machine()

    def _get_total_memory_bytes(self):
        system_name = platform.system()

        try:
            if system_name == 'Linux':
                with open('/proc/meminfo', 'r', encoding='utf-8') as file:
                    for line in file:
                        if line.startswith('MemTotal:'):
                            parts = line.split()
                            return int(parts[1]) * 1024

            if system_name == 'Darwin':
                output = self._run_command(['sysctl', '-n', 'hw.memsize'])
                return int(output)

            if system_name == 'Windows':
                output = self._run_command([
                    'powershell',
                    '-Command',
                    '(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory'
                ])
                return int(output)

        except (OSError, ValueError, subprocess.SubprocessError,
                FileNotFoundError):
            pass

        try:
            if hasattr(os, 'sysconf'):
                page_size = os.sysconf('SC_PAGE_SIZE')
                phys_pages = os.sysconf('SC_PHYS_PAGES')
                return page_size * phys_pages
        except (ValueError, OSError, AttributeError):
            pass

        return None

    def _read_linux_cpu_times(self):
        with open('/proc/stat', 'r', encoding='utf-8') as file:
            first_line = file.readline().strip()

        parts = first_line.split()
        values = []

        for value in parts[1:]:
            values.append(int(value))

        total_time = sum(values)
        idle_time = values[3]

        if len(values) > 4:
            idle_time += values[4]

        return total_time, idle_time

    def _get_linux_cpu_usage(self):
        total_1, idle_1 = self._read_linux_cpu_times()
        time.sleep(0.2)
        total_2, idle_2 = self._read_linux_cpu_times()

        total_diff = total_2 - total_1
        idle_diff = idle_2 - idle_1

        if total_diff <= 0:
            return None

        usage = (total_diff - idle_diff) / total_diff * 100
        return round(usage, 2)

    def _get_linux_memory_usage(self):
        mem_info = {}

        with open('/proc/meminfo', 'r', encoding='utf-8') as file:
            for line in file:
                if ':' not in line:
                    continue

                key, value = line.split(':', 1)
                mem_info[key.strip()] = int(value.strip().split()[0])

        total_kb = mem_info.get('MemTotal')
        available_kb = mem_info.get('MemAvailable')

        if total_kb is None or available_kb is None or total_kb == 0:
            return None

        used_kb = total_kb - available_kb
        usage = used_kb / total_kb * 100
        return round(usage, 2)

    def _get_mac_cpu_usage(self):
        output = self._run_command(['top', '-l', '1'])

        for line in output.splitlines():
            if 'CPU usage:' in line:
                parts = line.split(',')

                for part in parts:
                    text = part.strip()
                    if 'idle' in text:
                        idle_value = text.split('%')[0].split()[-1]
                        idle = float(idle_value)
                        return round(100 - idle, 2)

        return None

    def _get_mac_memory_usage(self):
        total_memory = self._get_total_memory_bytes()
        if total_memory is None or total_memory == 0:
            return None

        output = self._run_command(['vm_stat'])
        lines = output.splitlines()

        page_size = 4096
        if lines:
            first_line = lines[0]
            digits = ''
            for char in first_line:
                if char.isdigit():
                    digits += char
            if digits:
                page_size = int(digits)

        pages = {}

        for line in lines[1:]:
            if ':' not in line:
                continue

            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().replace('.', '')
            if value.isdigit():
                pages[key] = int(value)

        free_pages = pages.get('Pages free', 0)
        speculative_pages = pages.get('Pages speculative', 0)

        free_bytes = (free_pages + speculative_pages) * page_size
        used_bytes = total_memory - free_bytes

        usage = used_bytes / total_memory * 100
        return round(usage, 2)

    def _get_windows_cpu_usage(self):
        output = self._run_command([
            'powershell',
            '-Command',
            '(Get-Counter "\\Processor(_Total)\\% Processor Time").'
            'CounterSamples[0].CookedValue'
        ])
        return round(float(output), 2)

    def _get_windows_memory_usage(self):
        output = self._run_command([
            'powershell',
            '-Command',
            '$os = Get-CimInstance Win32_OperatingSystem; '
            '$usage = (($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) '
            '/ $os.TotalVisibleMemorySize) * 100; '
            '[math]::Round($usage, 2)'
        ])
        return float(output)

    def _get_cpu_usage(self):
        system_name = platform.system()

        try:
            if system_name == 'Linux':
                return self._get_linux_cpu_usage()

            if system_name == 'Darwin':
                return self._get_mac_cpu_usage()

            if system_name == 'Windows':
                return self._get_windows_cpu_usage()

        except (OSError, ValueError, subprocess.SubprocessError,
                FileNotFoundError):
            return None

        return None

    def _get_memory_usage(self):
        system_name = platform.system()

        try:
            if system_name == 'Linux':
                return self._get_linux_memory_usage()

            if system_name == 'Darwin':
                return self._get_mac_memory_usage()

            if system_name == 'Windows':
                return self._get_windows_memory_usage()

        except (OSError, ValueError, subprocess.SubprocessError,
                FileNotFoundError):
            return None

        return None

    def get_mission_computer_info(self):
        settings = self._load_settings()

        try:
            total_memory = self._get_total_memory_bytes()

            info = {
                'operating_system': platform.system(),
                'operating_system_version': platform.release(),
                'cpu_type': self._get_cpu_type(),
                'cpu_core_count': os.cpu_count(),
                'memory_size': self._format_size(total_memory)
            }

        except Exception as error:
            info = {
                'error': '시스템 정보를 가져오는 중 오류가 발생했습니다: {}'.format(
                    error
                )
            }

        selected_info = self._select_items(info, settings['info'])
        print(json.dumps(selected_info, ensure_ascii=False, indent=4))
        return selected_info

    def get_mission_computer_load(self):
        settings = self._load_settings()

        try:
            cpu_usage = self._get_cpu_usage()
            memory_usage = self._get_memory_usage()

            load = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage
            }

        except Exception as error:
            load = {
                'error': '시스템 부하 정보를 가져오는 중 오류가 발생했습니다: {}'.format(
                    error
                )
            }

        selected_load = self._select_items(load, settings['load'])
        print(json.dumps(selected_load, ensure_ascii=False, indent=4))
        return selected_load


runComputer = MissionComputer()
runComputer.get_mission_computer_info()
runComputer.get_mission_computer_load()