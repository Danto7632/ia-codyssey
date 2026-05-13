PASSWORD_FILE = 'password.txt'
RESULT_FILE = 'result.txt'
ALPHABET_COUNT = 26

WORD_LIST = [
    'mars',
    'base',
    'door',
    'open',
    'oxygen',
    'water',
    'emergency',
    'storage',
    'password',
    'key',
    'unlock'
]


def read_text_file(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(file_name + ' 파일을 찾을 수 없습니다.')
    except PermissionError:
        print(file_name + ' 파일을 읽을 권한이 없습니다.')
    except OSError:
        print(file_name + ' 파일을 읽는 중 오류가 발생했습니다.')

    return ''


def write_text_file(file_name, text):
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(text)
        print(file_name + ' 파일로 저장되었습니다.')
    except PermissionError:
        print(file_name + ' 파일을 저장할 권한이 없습니다.')
    except OSError:
        print(file_name + ' 파일을 저장하는 중 오류가 발생했습니다.')


def decode_character(char, shift):
    if 'a' <= char <= 'z':
        return chr((ord(char) - ord('a') - shift) % ALPHABET_COUNT + ord('a'))

    if 'A' <= char <= 'Z':
        return chr((ord(char) - ord('A') - shift) % ALPHABET_COUNT + ord('A'))

    return char


def check_dictionary(text):
    lower_text = text.lower()
    clean_text = ''

    for char in lower_text:
        if 'a' <= char <= 'z':
            clean_text += char
        else:
            clean_text += ' '

    text_words = clean_text.split()

    for word in WORD_LIST:
        if word in text_words:
            return word

    return ''


def caesar_cipher_decode(target_text):
    decoded_results = []

    for shift in range(ALPHABET_COUNT):
        decoded_text = ''

        for char in target_text:
            decoded_text += decode_character(char, shift)

        decoded_results.append(decoded_text)

        print('[' + str(shift) + '번 자리수]')
        print(decoded_text)
        print()

        found_word = check_dictionary(decoded_text)

        if found_word != '':
            print('사전 단어 "' + found_word + '"가 발견되었습니다.')
            print(str(shift) + '번 자리수에서 암호가 해독된 것으로 판단합니다.')
            write_text_file(RESULT_FILE, decoded_text)
            return decoded_results

    return decoded_results


def select_result(decoded_results):
    while True:
        selected_number = input('해독된 자리수 번호를 입력하세요: ')

        if selected_number.isdigit() is False:
            print('숫자만 입력해야 합니다.')
            continue

        selected_number = int(selected_number)

        if 0 <= selected_number < ALPHABET_COUNT:
            write_text_file(RESULT_FILE, decoded_results[selected_number])
            break

        print('0부터 25 사이의 숫자를 입력해야 합니다.')


def main():
    password_text = read_text_file(PASSWORD_FILE)

    if password_text == '':
        print('해독할 내용이 없습니다.')
        return

    decoded_results = caesar_cipher_decode(password_text)

    if len(decoded_results) == ALPHABET_COUNT:
        select_result(decoded_results)


if __name__ == '__main__':
    main()