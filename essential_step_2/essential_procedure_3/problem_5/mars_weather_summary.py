import binascii
import csv
import os
import struct
import zlib
from datetime import datetime

try:
    import mysql.connector
except ImportError:
    mysql = None
else:
    mysql = mysql.connector


HOST = 'localhost'
PORT = 3306
USER = 'root'
PASSWORD = 'mysql_password'
DATABASE = 'mars_db'
TABLE_NAME = 'mars_weather'

CSV_FILE_PATHS = (
    'mars_weathers_data.csv',
    'mars_weathers_data.CSV',
)

PNG_FILE_PATH = 'mars_weather_summary.png'


class MySQLHelper:
    def __init__(self, host, port, user, password, database=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        if mysql is None:
            raise ImportError(
                'mysql-connector-python 패키지를 설치해야 합니다.'
            )

        config = {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
        }

        if self.database is not None:
            config['database'] = self.database

        self.connection = mysql.connect(**config)
        self.connection.autocommit = False

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def execute(self, query, params=None):
        cursor = self.connection.cursor()

        try:
            cursor.execute(query, params)
        finally:
            cursor.close()

    def fetch_all(self, query, params=None):
        cursor = self.connection.cursor(dictionary=True)

        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        finally:
            cursor.close()

        return rows

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()


def find_csv_file():
    for file_path in CSV_FILE_PATHS:
        if os.path.exists(file_path):
            return file_path

    raise FileNotFoundError('mars_weathers_data.csv 파일을 찾을 수 없습니다.')


def normalize_date(date_text):
    date_text = date_text.strip()

    try:
        mars_date = datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        mars_date = datetime.fromisoformat(date_text)

    return mars_date.strftime('%Y-%m-%d %H:%M:%S')


def load_weather_data(file_path):
    weather_data = []

    with open(file_path, 'r', encoding='utf-8', newline='') as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise ValueError('CSV 파일에 헤더가 없습니다.')

        storm_key = 'storm'

        if 'storm' not in reader.fieldnames and 'stom' in reader.fieldnames:
            storm_key = 'stom'

        for row in reader:
            mars_date = normalize_date(row['mars_date'])
            temp = int(round(float(row['temp'])))
            storm = int(round(float(row[storm_key])))

            weather_data.append({
                'mars_date': mars_date,
                'temp': temp,
                'storm': storm,
            })

    return weather_data


def create_database():
    helper = MySQLHelper(HOST, PORT, USER, PASSWORD)

    try:
        helper.connect()
        helper.execute(
            f'CREATE DATABASE IF NOT EXISTS {DATABASE} '
            'DEFAULT CHARACTER SET utf8mb4 '
            'DEFAULT COLLATE utf8mb4_unicode_ci'
        )
        helper.commit()
    finally:
        helper.close()


def create_weather_table(helper):
    query = f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            weather_id INT NOT NULL AUTO_INCREMENT,
            mars_date DATETIME NOT NULL,
            temp INT,
            storm INT,
            PRIMARY KEY (weather_id)
        )
    '''

    helper.execute(query)


def clear_weather_table(helper):
    helper.execute(f'TRUNCATE TABLE {TABLE_NAME}')


def insert_weather_data(helper, weather_data):
    query = f'''
        INSERT INTO {TABLE_NAME} (
            mars_date,
            temp,
            storm
        ) VALUES (
            %s,
            %s,
            %s
        )
    '''

    for weather in weather_data:
        params = (
            weather['mars_date'],
            weather['temp'],
            weather['storm'],
        )
        helper.execute(query, params)


def fetch_weather_data(helper):
    query = f'''
        SELECT
            mars_date,
            temp,
            storm
        FROM {TABLE_NAME}
        ORDER BY mars_date
    '''

    return helper.fetch_all(query)


def make_png_chunk(chunk_type, data):
    crc = binascii.crc32(chunk_type + data) & 0xffffffff

    return (
        struct.pack('>I', len(data))
        + chunk_type
        + data
        + struct.pack('>I', crc)
    )


def save_png(file_path, pixels, width, height):
    raw_data = bytearray()

    for y in range(height):
        raw_data.append(0)

        for x in range(width):
            raw_data.extend(pixels[y][x])

    png_data = bytearray()
    png_data.extend(b'\x89PNG\r\n\x1a\n')
    png_data.extend(make_png_chunk(
        b'IHDR',
        struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ))
    png_data.extend(make_png_chunk(
        b'IDAT',
        zlib.compress(bytes(raw_data), 9)
    ))
    png_data.extend(make_png_chunk(b'IEND', b''))

    with open(file_path, 'wb') as png_file:
        png_file.write(png_data)


def create_canvas(width, height, color):
    pixels = []

    for _ in range(height):
        row = []

        for _ in range(width):
            row.append(bytearray(color))

        pixels.append(row)

    return pixels


def set_pixel(pixels, x, y, color):
    height = len(pixels)
    width = len(pixels[0])

    if 0 <= x < width and 0 <= y < height:
        pixels[y][x] = bytearray(color)


def draw_line(pixels, start_x, start_y, end_x, end_y, color):
    dx = abs(end_x - start_x)
    dy = -abs(end_y - start_y)

    step_x = 1

    if start_x >= end_x:
        step_x = -1

    step_y = 1

    if start_y >= end_y:
        step_y = -1

    error = dx + dy
    x = start_x
    y = start_y

    while True:
        set_pixel(pixels, x, y, color)

        if x == end_x and y == end_y:
            break

        error_value = 2 * error

        if error_value >= dy:
            error += dy
            x += step_x

        if error_value <= dx:
            error += dx
            y += step_y


def draw_rect(pixels, left, top, right, bottom, color):
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            set_pixel(pixels, x, y, color)


def scale_value(value, min_value, max_value, bottom, top):
    if max_value == min_value:
        return bottom

    ratio = (value - min_value) / (max_value - min_value)

    return int(bottom - ratio * (bottom - top))


def make_weather_summary_png(weather_data, file_path):
    width = 1000
    height = 500
    margin = 50
    chart_left = margin
    chart_right = width - margin
    chart_top = margin
    chart_bottom = height - margin

    white = (255, 255, 255)
    black = (0, 0, 0)
    gray = (220, 220, 220)
    blue = (70, 120, 220)
    orange = (245, 150, 40)

    pixels = create_canvas(width, height, white)

    draw_line(pixels, chart_left, chart_bottom, chart_right, chart_bottom, black)
    draw_line(pixels, chart_left, chart_top, chart_left, chart_bottom, black)

    for i in range(1, 5):
        y = chart_top + i * (chart_bottom - chart_top) // 5
        draw_line(pixels, chart_left, y, chart_right, y, gray)

    temps = [weather['temp'] for weather in weather_data]
    storms = [weather['storm'] for weather in weather_data]

    min_temp = min(temps)
    max_temp = max(temps)
    max_storm = max(storms)

    previous_x = None
    previous_y = None
    total_count = len(weather_data)

    for index, weather in enumerate(weather_data):
        x = chart_left + int(
            index * (chart_right - chart_left) / (total_count - 1)
        )

        temp_y = scale_value(
            weather['temp'],
            min_temp,
            max_temp,
            chart_bottom,
            chart_top,
        )

        storm_height = 0

        if max_storm > 0:
            storm_height = int(
                weather['storm'] * (chart_bottom - chart_top) / max_storm
            )

        storm_top = chart_bottom - storm_height

        if weather['storm'] >= 70:
            draw_line(pixels, x, chart_bottom, x, storm_top, orange)

        if previous_x is not None and previous_y is not None:
            draw_line(pixels, previous_x, previous_y, x, temp_y, blue)

        previous_x = x
        previous_y = temp_y

    legend_top = 15
    draw_rect(pixels, 50, legend_top, 80, legend_top + 10, blue)
    draw_rect(pixels, 220, legend_top, 250, legend_top + 10, orange)

    save_png(file_path, pixels, width, height)


def print_summary(weather_data):
    temps = [weather['temp'] for weather in weather_data]
    storms = [weather['storm'] for weather in weather_data]
    storm_days = 0

    for storm in storms:
        if storm >= 70:
            storm_days += 1

    print('화성 날씨 데이터 요약')
    print(f'전체 데이터 수: {len(weather_data)}')
    print(f'최저 기온: {min(temps)}')
    print(f'최고 기온: {max(temps)}')
    print(f'평균 기온: {sum(temps) / len(temps):.2f}')
    print(f'모래 폭풍 위험일 수: {storm_days}')


def main():
    csv_file_path = find_csv_file()
    weather_data = load_weather_data(csv_file_path)

    print_summary(weather_data)

    create_database()

    helper = MySQLHelper(HOST, PORT, USER, PASSWORD, DATABASE)

    try:
        helper.connect()
        create_weather_table(helper)
        clear_weather_table(helper)
        insert_weather_data(helper, weather_data)
        helper.commit()

        saved_weather_data = fetch_weather_data(helper)
        make_weather_summary_png(saved_weather_data, PNG_FILE_PATH)

        print(f'{len(saved_weather_data)}개의 데이터를 저장했습니다.')
        print(f'{PNG_FILE_PATH} 파일을 생성했습니다.')
    except Exception:
        helper.rollback()
        raise
    finally:
        helper.close()


if __name__ == '__main__':
    main()