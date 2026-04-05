import time
import threading


class DummySensor:
    def __init__(self):
        self.env_values = {
            'mars_base_internal_temperature': 0.0,
            'mars_base_external_temperature': 0.0,
            'mars_base_internal_humidity': 0.0,
            'mars_base_external_illuminance': 0.0,
            'mars_base_internal_co2': 0.0,
            'mars_base_internal_oxygen': 0.0
        }
        self.seed = 12345

    def _make_value(self, min_value, max_value, decimal_places):
        self.seed = (self.seed * 1103515245 + 12345) % 2147483648
        ratio = self.seed / 2147483648
        value = min_value + (max_value - min_value) * ratio
        return round(value, decimal_places)

    def set_env(self):
        self.env_values['mars_base_internal_temperature'] = self._make_value(
            18, 30, 2
        )
        self.env_values['mars_base_external_temperature'] = self._make_value(
            0, 21, 2
        )
        self.env_values['mars_base_internal_humidity'] = self._make_value(
            50, 60, 2
        )
        self.env_values['mars_base_external_illuminance'] = self._make_value(
            500, 715, 2
        )
        self.env_values['mars_base_internal_co2'] = self._make_value(
            0.02, 0.1, 4
        )
        self.env_values['mars_base_internal_oxygen'] = self._make_value(
            4, 7, 2
        )

    def get_env(self):
        date_time = '2099-03-15 14:30:00'

        log_text = (
            date_time + ', '
            + str(self.env_values['mars_base_internal_temperature']) + ', '
            + str(self.env_values['mars_base_external_temperature']) + ', '
            + str(self.env_values['mars_base_internal_humidity']) + ', '
            + str(self.env_values['mars_base_external_illuminance']) + ', '
            + str(self.env_values['mars_base_internal_co2']) + ', '
            + str(self.env_values['mars_base_internal_oxygen']) + '\n'
        )

        with open('mars_mission_log.txt', 'a', encoding='utf-8') as file:
            file.write(log_text)

        return self.env_values


ds = DummySensor()


class MissionComputer:
    def __init__(self):
        self.env_values = {
            'mars_base_internal_temperature': 0.0,
            'mars_base_external_temperature': 0.0,
            'mars_base_internal_humidity': 0.0,
            'mars_base_external_illuminance': 0.0,
            'mars_base_internal_co2': 0.0,
            'mars_base_internal_oxygen': 0.0
        }
        self.average_values = {
            'mars_base_internal_temperature': 0.0,
            'mars_base_external_temperature': 0.0,
            'mars_base_internal_humidity': 0.0,
            'mars_base_external_illuminance': 0.0,
            'mars_base_internal_co2': 0.0,
            'mars_base_internal_oxygen': 0.0
        }
        self.history = []
        self.running = True

    def _dict_to_json_text(self, data):
        lines = ['{']
        items = list(data.items())

        for index, (key, value) in enumerate(items):
            if index < len(items) - 1:
                line = '    ' + '"' + key + '"' + ': ' + str(value) + ','
            else:
                line = '    ' + '"' + key + '"' + ': ' + str(value)
            lines.append(line)

        lines.append('}')
        return '\n'.join(lines)

    def _save_history(self):
        self.history.append(self.env_values.copy())

    def _print_average_values(self):
        if len(self.history) == 0:
            return

        for key in self.average_values:
            total = 0.0

            for item in self.history:
                total += item[key]

            self.average_values[key] = round(total / len(self.history), 4)

        print('5 minute average values')
        print(self._dict_to_json_text(self.average_values))

    def _check_stop_input(self):
        while self.running:
            user_input = input()

            if user_input.lower() == 'q':
                self.running = False
                print('Sytem stoped....')
                break

    def get_sensor_data(self):
        input_thread = threading.Thread(target = self._check_stop_input)
        input_thread.daemon = True
        input_thread.start()

        start_time = time.time()
        average_start_time = time.time()

        while self.running:
            ds.set_env()
            sensor_values = ds.get_env()

            for key in self.env_values:
                self.env_values[key] = sensor_values[key]

            print(self._dict_to_json_text(self.env_values))
            self._save_history()

            current_time = time.time()

            if current_time - average_start_time >= 300:
                self._print_average_values()
                self.history = []
                average_start_time = current_time

            elapsed_time = time.time() - current_time

            if elapsed_time < 5:
                time.sleep(5 - elapsed_time)


RunComputer = MissionComputer()
RunComputer.get_sensor_data()