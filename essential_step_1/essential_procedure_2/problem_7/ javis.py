from datetime import datetime
import os
import wave

try:
    import sounddevice as sd
except ImportError:
    sd = None


RECORD_DIR = 'records'
SAMPLE_RATE = 44100
CHANNELS = 1
SAMPLE_WIDTH = 2


def make_records_folder():
    if not os.path.exists(RECORD_DIR):
        os.mkdir(RECORD_DIR)


def make_file_name():
    now = datetime.now()
    return now.strftime('%Y%m%d-%H%M%S') + '.wav'


def make_file_path():
    file_name = make_file_name()
    return os.path.join(RECORD_DIR, file_name)


def show_input_devices():
    if sd is None:
        return []

    devices = sd.query_devices()
    input_devices = []

    print('\n[사용 가능한 마이크 목록]')

    for index, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append(index)
            print(str(index) + '. ' + device['name'])

    if len(input_devices) == 0:
        print('사용 가능한 마이크가 없습니다.')

    return input_devices


def select_input_device(input_devices):
    if len(input_devices) == 0:
        return None

    selected = input('사용할 마이크 번호를 입력하세요: ')

    if not selected.isdigit():
        print('숫자만 입력해야 합니다.')
        return None

    selected = int(selected)

    if selected not in input_devices:
        print('목록에 없는 마이크 번호입니다.')
        return None

    return selected


def get_record_seconds():
    seconds = input('녹음할 시간을 초 단위로 입력하세요: ')

    if not seconds.isdigit():
        print('녹음 시간은 숫자로 입력해야 합니다.')
        return 0

    seconds = int(seconds)

    if seconds <= 0:
        print('녹음 시간은 1초 이상이어야 합니다.')
        return 0

    return seconds


def save_record_file(file_path, record_data):
    with wave.open(file_path, 'wb') as file:
        file.setnchannels(CHANNELS)
        file.setsampwidth(SAMPLE_WIDTH)
        file.setframerate(SAMPLE_RATE)
        file.writeframes(record_data.tobytes())


def record_voice():
    if sd is None:
        print('sounddevice 라이브러리가 설치되어 있지 않습니다.')
        print('pip install sounddevice 명령어로 설치할 수 있습니다.')
        return

    make_records_folder()

    input_devices = show_input_devices()
    device_index = select_input_device(input_devices)

    if device_index is None:
        return

    seconds = get_record_seconds()

    if seconds == 0:
        return

    file_path = make_file_path()

    print('\n녹음을 시작합니다.')
    record_data = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='int16',
        device=device_index
    )

    sd.wait()

    save_record_file(file_path, record_data)

    print('녹음이 완료되었습니다.')
    print('저장 위치: ' + file_path)


def is_valid_date(date_text):
    if len(date_text) != 8:
        return False

    if not date_text.isdigit():
        return False

    try:
        datetime.strptime(date_text, '%Y%m%d')
    except ValueError:
        return False

    return True


def show_records_by_date():
    make_records_folder()

    start_date = input('시작 날짜를 입력하세요. 예: 20260518: ')
    end_date = input('끝 날짜를 입력하세요. 예: 20260520: ')

    if not is_valid_date(start_date) or not is_valid_date(end_date):
        print('날짜 형식이 올바르지 않습니다.')
        return

    if start_date > end_date:
        print('시작 날짜가 끝 날짜보다 늦을 수 없습니다.')
        return

    files = os.listdir(RECORD_DIR)
    matched_files = []

    for file_name in files:
        if not file_name.endswith('.wav'):
            continue

        file_date = file_name[:8]

        if start_date <= file_date <= end_date:
            matched_files.append(file_name)

    if len(matched_files) == 0:
        print('해당 날짜 범위의 녹음 파일이 없습니다.')
        return

    matched_files.sort()

    print('\n[녹음 파일 목록]')

    for file_name in matched_files:
        print(file_name)


def show_menu():
    print('\n[JAVIS 음성 기록 시스템]')
    print('1. 음성 녹음하기')
    print('2. 날짜 범위로 녹음 파일 보기')
    print('3. 종료')


def run_javis():
    while True:
        show_menu()
        menu = input('메뉴를 선택하세요: ')

        if menu == '1':
            record_voice()
        elif menu == '2':
            show_records_by_date()
        elif menu == '3':
            print('JAVIS를 종료합니다.')
            break
        else:
            print('올바른 메뉴를 선택하세요.')


if __name__ == '__main__':
    run_javis()