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
ds.set_env()
print(ds.get_env())