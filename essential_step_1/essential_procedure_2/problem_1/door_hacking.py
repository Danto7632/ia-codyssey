import multiprocessing
import time
import zipfile


ZIP_FILE = 'emergency_storage_key.zip'
PASSWORD_FILE = 'password.txt'

PASSWORD_LENGTH = 6
CHARACTERS = '0123456789abcdefghijklmnopqrstuvwxyz'
PRINT_INTERVAL = 1000000


def make_elapsed_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    return str(hours) + '시간 ' + str(minutes) + '분 ' + str(secs) + '초'


def get_cpu_count():
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        return 1


def number_to_indexes(number):
    indexes = [0] * PASSWORD_LENGTH
    position = PASSWORD_LENGTH - 1

    while position >= 0:
        indexes[position] = number % len(CHARACTERS)
        number = number // len(CHARACTERS)
        position = position - 1

    return indexes


def increase_password(indexes):
    position = PASSWORD_LENGTH - 1

    while position >= 0:
        indexes[position] = indexes[position] + 1

        if indexes[position] < len(CHARACTERS):
            return True

        indexes[position] = 0
        position = position - 1

    return False


def make_password_from_indexes(indexes):
    password = ''

    for index in indexes:
        password = password + CHARACTERS[index]

    return password


def find_smallest_file(zip_file):
    file_infos = zip_file.infolist()
    smallest_file = None

    for file_info in file_infos:
        if file_info.filename.endswith('/'):
            continue

        if file_info.file_size == 0:
            continue

        if smallest_file is None:
            smallest_file = file_info
        elif file_info.compress_size < smallest_file.compress_size:
            smallest_file = file_info

    if smallest_file is not None:
        return smallest_file.filename

    for file_info in file_infos:
        if not file_info.filename.endswith('/'):
            return file_info.filename

    return None


def print_progress(
    worker_id,
    local_count,
    total_count,
    total,
    password,
    start_time
):
    elapsed_time = time.time() - start_time

    print('작업 번호:', worker_id)
    print('작업 반복 회수:', local_count)
    print('전체 누적 반복 회수:', total_count)
    print('전체 경우의 수:', total)
    print('현재 시도 암호:', password)
    print('진행 시간:', make_elapsed_time(elapsed_time))
    print('-' * 30)


def try_password(zip_file, target_file, password):
    try:
        zip_file.read(target_file, pwd=password.encode('utf-8'))
        return True
    except Exception:
        return False


def save_password(password):
    try:
        with open(PASSWORD_FILE, 'w', encoding='utf-8') as file:
            file.write(password)
    except OSError as error:
        print('password.txt 저장 중 오류가 발생했습니다.')
        print(error)
        return False

    return True


def update_total_count(total_count, lock, value):
    with lock:
        total_count.value = total_count.value + value
        return total_count.value


def worker_unlock_zip(
    worker_id,
    start_number,
    end_number,
    target_file,
    stop_event,
    result_queue,
    total_count,
    lock,
    start_time
):
    indexes = number_to_indexes(start_number)
    current_number = start_number
    local_count = 0
    update_count = 0
    total = len(CHARACTERS) ** PASSWORD_LENGTH

    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_file:
            while current_number < end_number:
                if stop_event.is_set():
                    break

                password = make_password_from_indexes(indexes)
                local_count = local_count + 1
                update_count = update_count + 1

                if update_count >= PRINT_INTERVAL:
                    current_total = update_total_count(
                        total_count,
                        lock,
                        update_count
                    )
                    update_count = 0

                    with lock:
                        print_progress(
                            worker_id,
                            local_count,
                            current_total,
                            total,
                            password,
                            start_time
                        )

                if try_password(zip_file, target_file, password):
                    current_total = update_total_count(
                        total_count,
                        lock,
                        update_count
                    )

                    with lock:
                        print_progress(
                            worker_id,
                            local_count,
                            current_total,
                            total,
                            password,
                            start_time
                        )

                    result_queue.put((worker_id, password, local_count))
                    stop_event.set()
                    return

                current_number = current_number + 1

                if current_number < end_number:
                    increase_password(indexes)

    except FileNotFoundError:
        result_queue.put((worker_id, None, local_count))
        stop_event.set()
        return
    except zipfile.BadZipFile:
        result_queue.put((worker_id, None, local_count))
        stop_event.set()
        return
    except OSError:
        result_queue.put((worker_id, None, local_count))
        stop_event.set()
        return

    if update_count > 0:
        update_total_count(total_count, lock, update_count)


def make_ranges(total, worker_count):
    ranges = []
    start_number = 0
    base_size = total // worker_count
    remainder = total % worker_count

    for worker_id in range(worker_count):
        extra = 0

        if worker_id < remainder:
            extra = 1

        end_number = start_number + base_size + extra
        ranges.append((worker_id + 1, start_number, end_number))
        start_number = end_number

    return ranges


def check_zip_file():
    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_file:
            target_file = find_smallest_file(zip_file)

            if target_file is None:
                print('zip 파일 안에 검사할 파일이 없습니다.')
                return None

            return target_file

    except FileNotFoundError:
        print(ZIP_FILE + ' 파일을 찾을 수 없습니다.')
        return None
    except zipfile.BadZipFile:
        print('정상적인 zip 파일이 아닙니다.')
        return None
    except OSError as error:
        print('파일을 처리하는 중 오류가 발생했습니다.')
        print(error)
        return None


def stop_processes(processes):
    for process in processes:
        if process.is_alive():
            process.terminate()

    for process in processes:
        process.join()


def unlock_zip():
    start_time = time.time()
    start_text = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
    total = len(CHARACTERS) ** PASSWORD_LENGTH
    worker_count = get_cpu_count() - 1
    target_file = check_zip_file()

    if worker_count < 1:
        worker_count = 1

    if target_file is None:
        return None

    stop_event = multiprocessing.Event()
    result_queue = multiprocessing.Queue()
    total_count = multiprocessing.Value('q', 0)
    lock = multiprocessing.Lock()
    processes = []
    ranges = make_ranges(total, worker_count)

    print('암호 해독을 시작합니다.')
    print('시작 시간:', start_text)
    print('사용 CPU 코어 수:', worker_count)
    print('전체 경우의 수:', total)
    print('검사 대상 파일:', target_file)
    print('-' * 30)

    for worker_id, start_number, end_number in ranges:
        process = multiprocessing.Process(
            target=worker_unlock_zip,
            args=(
                worker_id,
                start_number,
                end_number,
                target_file,
                stop_event,
                result_queue,
                total_count,
                lock,
                start_time
            )
        )

        processes.append(process)
        process.start()

    found_result = None

    while True:
        if not result_queue.empty():
            found_result = result_queue.get()
            break

        is_running = False

        for process in processes:
            if process.is_alive():
                is_running = True
                break

        if not is_running:
            break

        time.sleep(0.2)

    if found_result is not None:
        worker_id, password, local_count = found_result

        if password is not None:
            stop_event.set()
            stop_processes(processes)

            if save_password(password):
                print('암호 해독에 성공했습니다.')
                print('성공 작업 번호:', worker_id)
                print('성공 작업 반복 회수:', local_count)
                print('찾은 암호:', password)
                print('password.txt 파일로 저장했습니다.')
                return password

            print('암호는 찾았지만 password.txt 저장에 실패했습니다.')
            print('찾은 암호:', password)
            return password

    stop_processes(processes)
    print('암호를 찾지 못했습니다.')
    return None


if __name__ == '__main__':
    multiprocessing.freeze_support()
    unlock_zip()