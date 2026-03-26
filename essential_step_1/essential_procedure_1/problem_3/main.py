INPUT_FILE = 'Mars_Base_Inventory_List.csv'
DANGER_FILE = 'Mars_Base_Inventory_danger.csv'
BINARY_FILE = 'Mars_Base_Inventory_List.bin'

FLAMMABILITY_CANDIDATES = [
    'flammability',
    'flammability_index',
    'fire_risk',
    'hazard_level',
    'hazard_score',
    '인화성',
    '인화성지수'
]


def normalize_text(text):
    return str(text).strip().lower().replace(' ', '').replace('_', '').replace('-', '')


def to_float(value):
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return -1.0


def find_flammability_column(headers):
    normalized_candidates = []

    for item in FLAMMABILITY_CANDIDATES:
        normalized_candidates.append(normalize_text(item))

    for header in headers:
        if normalize_text(header) in normalized_candidates:
            return header

    for header in headers:
        normalized_header = normalize_text(header)
        if 'flamm' in normalized_header or '인화성' in header:
            return header

    return None


def read_csv_file(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f'오류: {file_name} 파일을 찾을 수 없습니다.')
        return [], []
    except PermissionError:
        print(f'오류: {file_name} 파일에 접근 권한이 없습니다.')
        return [], []
    except OSError as error:
        print(f'오류: 파일 읽기 중 문제가 발생했습니다. {error}')
        return [], []

    if not lines:
        return [], []

    headers = lines[0].strip().split(',')
    cleaned_headers = []

    for header in headers:
        cleaned_headers.append(header.strip())

    data_list = []

    for line in lines[1:]:
        line = line.strip()

        if line == '':
            continue

        values = line.split(',')
        row = {}

        for index in range(len(cleaned_headers)):
            key = cleaned_headers[index]

            if index < len(values):
                row[key] = values[index].strip()
            else:
                row[key] = ''

        data_list.append(row)

    return cleaned_headers, data_list


def print_rows(title, rows):
    print(f'\n[{title}]')

    if not rows:
        print('데이터가 없습니다.')
        return

    for index, row in enumerate(rows, start=1):
        print(f'{index}. {row}')


def sort_by_flammability(data_list, column_name):
    return sorted(
        data_list,
        key=lambda row: to_float(row.get(column_name)),
        reverse=True
    )


def filter_danger_items(data_list, column_name, threshold):
    result = []

    for row in data_list:
        if to_float(row.get(column_name)) >= threshold:
            result.append(row)

    return result


def save_csv_file(file_name, headers, rows):
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(','.join(headers) + '\n')

            for row in rows:
                values = []

                for header in headers:
                    values.append(str(row.get(header, '')))

                file.write(','.join(values) + '\n')

        print(f'\n저장 완료: {file_name}')
    except PermissionError:
        print(f'오류: {file_name} 파일에 쓸 권한이 없습니다.')
    except OSError as error:
        print(f'오류: CSV 저장 중 문제가 발생했습니다. {error}')


def save_binary_file(file_name, headers, rows):
    try:
        text_data = ','.join(headers) + '\n'

        for row in rows:
            values = []

            for header in headers:
                values.append(str(row.get(header, '')))

            text_data += ','.join(values) + '\n'

        with open(file_name, 'wb') as file:
            file.write(text_data.encode('utf-8'))

        print(f'저장 완료: {file_name}')
    except PermissionError:
        print(f'오류: {file_name} 파일에 쓸 권한이 없습니다.')
    except OSError as error:
        print(f'오류: 이진 파일 저장 중 문제가 발생했습니다. {error}')


def load_binary_file(file_name):
    try:
        with open(file_name, 'rb') as file:
            binary_data = file.read()

        text_data = binary_data.decode('utf-8')
        lines = text_data.splitlines()
    except FileNotFoundError:
        print(f'오류: {file_name} 파일을 찾을 수 없습니다.')
        return [], []
    except PermissionError:
        print(f'오류: {file_name} 파일에 접근 권한이 없습니다.')
        return [], []
    except OSError as error:
        print(f'오류: 이진 파일 읽기 중 문제가 발생했습니다. {error}')
        return [], []

    if not lines:
        return [], []

    headers = lines[0].strip().split(',')
    cleaned_headers = []

    for header in headers:
        cleaned_headers.append(header.strip())

    data_list = []

    for line in lines[1:]:
        line = line.strip()

        if line == '':
            continue

        values = line.split(',')
        row = {}

        for index in range(len(cleaned_headers)):
            key = cleaned_headers[index]

            if index < len(values):
                row[key] = values[index].strip()
            else:
                row[key] = ''

        data_list.append(row)

    return cleaned_headers, data_list


def main():
    headers, inventory_list = read_csv_file(INPUT_FILE)

    if not inventory_list:
        print('데이터가 없어서 프로그램을 종료합니다.')
        return

    print_rows('원본 CSV 내용', inventory_list)

    print('\n[리스트 객체 변환 결과]')
    print(inventory_list)

    flammability_column = find_flammability_column(headers)

    if flammability_column is None:
        print('\n오류: 인화성 지수 컬럼을 찾지 못했습니다.')
        return

    print(f'\n인화성 기준 컬럼: {flammability_column}')

    sorted_list = sort_by_flammability(inventory_list, flammability_column)
    print_rows('인화성이 높은 순으로 정렬한 결과', sorted_list)

    danger_list = filter_danger_items(sorted_list, flammability_column, 0.7)
    print_rows('인화성 지수 0.7 이상 목록', danger_list)

    save_csv_file(DANGER_FILE, headers, danger_list)

    save_binary_file(BINARY_FILE, headers, sorted_list)

    loaded_headers, loaded_list = load_binary_file(BINARY_FILE)

    if loaded_headers and loaded_list:
        print_rows('이진 파일에서 다시 읽어온 내용', loaded_list)


if __name__ == '__main__':
    main()