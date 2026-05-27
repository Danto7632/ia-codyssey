import csv
import os
import wave

import speech_recognition as sr


RECORD_DIR = 'records'
AUDIO_EXTENSION = '.wav'
CSV_EXTENSION = '.CSV'
CHUNK_SECONDS = 10


def get_audio_files():
    audio_files = []

    if not os.path.exists(RECORD_DIR):
        print('녹음 파일 폴더가 없습니다.')
        return audio_files

    file_names = os.listdir(RECORD_DIR)

    for file_name in file_names:
        if file_name.lower().endswith(AUDIO_EXTENSION):
            audio_files.append(file_name)

    return audio_files


def print_audio_files(audio_files):
    if len(audio_files) == 0:
        print('녹음된 음성 파일이 없습니다.')
        return

    print('녹음된 음성 파일 목록')

    for index, file_name in enumerate(audio_files):
        print(str(index + 1) + '. ' + file_name)


def get_wav_duration(file_path):
    with wave.open(file_path, 'rb') as wav_file:
        frame_count = wav_file.getnframes()
        frame_rate = wav_file.getframerate()

        if frame_rate == 0:
            return 0

        return frame_count / frame_rate


def format_time(seconds):
    seconds = int(seconds)

    hour = seconds // 3600
    minute = (seconds % 3600) // 60
    second = seconds % 60

    return (
        str(hour).zfill(2)
        + ':'
        + str(minute).zfill(2)
        + ':'
        + str(second).zfill(2)
    )


def make_csv_file_path(audio_file_name):
    file_name_without_extension = os.path.splitext(audio_file_name)[0]
    csv_file_name = file_name_without_extension + CSV_EXTENSION

    return os.path.join(RECORD_DIR, csv_file_name)


def recognize_audio_chunk(file_path, start_time, duration):
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(file_path) as audio_source:
            audio_data = recognizer.record(
                audio_source,
                offset=start_time,
                duration=duration
            )

        text = recognizer.recognize_google(audio_data, language='ko-KR')
        return text

    except sr.UnknownValueError:
        return ''

    except sr.RequestError:
        print('STT 서비스 요청 중 문제가 발생했습니다.')
        return ''

    except Exception as error:
        print('음성 인식 중 오류가 발생했습니다.')
        print(error)
        return ''


def save_stt_result_to_csv(audio_file_name):
    audio_file_path = os.path.join(RECORD_DIR, audio_file_name)
    csv_file_path = make_csv_file_path(audio_file_name)

    duration = get_wav_duration(audio_file_path)
    current_time = 0
    stt_results = []

    print('STT 변환을 시작합니다.')
    print('대상 파일: ' + audio_file_name)

    while current_time < duration:
        remain_time = duration - current_time

        if remain_time < CHUNK_SECONDS:
            chunk_duration = remain_time
        else:
            chunk_duration = CHUNK_SECONDS

        text = recognize_audio_chunk(
            audio_file_path,
            current_time,
            chunk_duration
        )

        if text != '':
            stt_results.append([format_time(current_time), text])
            print(format_time(current_time) + ' - ' + text)

        current_time = current_time + CHUNK_SECONDS

    with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['time', 'recognized_text'])
        writer.writerows(stt_results)

    print('CSV 저장이 완료되었습니다.')
    print('저장 파일: ' + csv_file_path)


def select_audio_file(audio_files):
    print_audio_files(audio_files)

    if len(audio_files) == 0:
        return ''

    selected = input('STT로 변환할 파일 번호를 입력하세요: ')

    if not selected.isdigit():
        print('숫자를 입력해야 합니다.')
        return ''

    selected_index = int(selected) - 1

    if selected_index < 0 or selected_index >= len(audio_files):
        print('잘못된 번호입니다.')
        return ''

    return audio_files[selected_index]


def get_csv_files():
    csv_files = []

    if not os.path.exists(RECORD_DIR):
        return csv_files

    file_names = os.listdir(RECORD_DIR)

    for file_name in file_names:
        if file_name.endswith(CSV_EXTENSION):
            csv_files.append(file_name)

    return csv_files


def search_keyword_in_csv():
    keyword = input('검색할 키워드를 입력하세요: ')

    if keyword == '':
        print('검색어가 비어 있습니다.')
        return

    csv_files = get_csv_files()

    if len(csv_files) == 0:
        print('검색할 CSV 파일이 없습니다.')
        return

    found_count = 0

    for csv_file_name in csv_files:
        csv_file_path = os.path.join(RECORD_DIR, csv_file_name)

        with open(csv_file_path, 'r', encoding='utf-8-sig') as csv_file:
            reader = csv.reader(csv_file)
            next(reader, None)

            for row in reader:
                if len(row) < 2:
                    continue

                record_time = row[0]
                recognized_text = row[1]

                if keyword in recognized_text:
                    print('파일: ' + csv_file_name)
                    print('시간: ' + record_time)
                    print('내용: ' + recognized_text)
                    print('-' * 30)
                    found_count = found_count + 1

    if found_count == 0:
        print('검색 결과가 없습니다.')
    else:
        print('총 ' + str(found_count) + '개의 결과를 찾았습니다.')


def run_stt_menu():
    while True:
        print()
        print('JAVIS 음성 기록 관리')
        print('1. 녹음 파일 목록 보기')
        print('2. 음성 파일 STT 변환')
        print('3. CSV 기록 검색')
        print('4. 종료')

        selected_menu = input('메뉴를 선택하세요: ')

        if selected_menu == '1':
            audio_files = get_audio_files()
            print_audio_files(audio_files)

        elif selected_menu == '2':
            audio_files = get_audio_files()
            audio_file_name = select_audio_file(audio_files)

            if audio_file_name != '':
                save_stt_result_to_csv(audio_file_name)

        elif selected_menu == '3':
            search_keyword_in_csv()

        elif selected_menu == '4':
            print('JAVIS 음성 기록 관리를 종료합니다.')
            break

        else:
            print('잘못된 메뉴입니다.')


if __name__ == '__main__':
    run_stt_menu()