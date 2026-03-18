LOG_FILE = 'mission_computer_main.log'
REVERSE_FILE = 'mission_computer_main_reverse.log'
PROBLEM_FILE = 'mission_computer_main_problem.log'
REPORT_FILE = 'log_analysis.md'

PROBLEM_KEYWORDS = [
    'error',
    'fail',
    'failed',
    'critical',
    'warning',
    'warn',
    'exception',
    'fault',
    'shutdown',
    'explode',
    'explosion',
    'overheat',
    'leak',
    'pressure',
    'power loss',
    'low oxygen',
    'oxygen',
    'temperature'
]


def print_hello():
    print('Hello Mars')


def read_log_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        return file.readlines()


def print_log(lines):
    print('===== mission_computer_main.log 전체 내용 =====')
    for line in lines:
        print(line, end='')
    print('\n===== 출력 종료 =====')


def is_digit_string(text):
    if text == '':
        return False

    for char in text:
        if not ('0' <= char <= '9'):
            return False

    return True


def extract_sort_key(line):
    text = line.strip()

    if len(text) >= 19:
        date_part = text[0:10]
        time_part = text[11:19]

        is_date_format = (
            date_part[4] == '-'
            and date_part[7] == '-'
            and is_digit_string(date_part[0:4])
            and is_digit_string(date_part[5:7])
            and is_digit_string(date_part[8:10])
        )

        is_time_format = (
            time_part[2] == ':'
            and time_part[5] == ':'
            and is_digit_string(time_part[0:2])
            and is_digit_string(time_part[3:5])
            and is_digit_string(time_part[6:8])
        )

        if is_date_format and is_time_format:
            if text[10] == ' ' or text[10] == 'T':
                return text[0:19]

    first_space_index = text.find(' ')
    if first_space_index != -1:
        return text[:first_space_index]

    return text


def has_sortable_timestamp(lines):
    for line in lines:
        stripped = line.strip()

        if stripped == '':
            continue

        sort_key = extract_sort_key(stripped)
        if len(sort_key) == 19:
            if sort_key[4] == '-' and sort_key[7] == '-':
                return True

    return False


def reverse_by_time(lines):
    if has_sortable_timestamp(lines):
        return sorted(lines, key=extract_sort_key, reverse=True)

    return list(reversed(lines))


def save_lines(file_name, lines):
    with open(file_name, 'w', encoding='utf-8') as file:
        for line in lines:
            file.write(line)


def collect_problem_lines(lines):
    problem_entries = []
    keyword_counts = {}

    for keyword in PROBLEM_KEYWORDS:
        keyword_counts[keyword] = 0

    for line_number, line in enumerate(lines, start=1):
        lower_line = line.lower()
        matched_keywords = []

        for keyword in PROBLEM_KEYWORDS:
            if keyword in lower_line:
                keyword_counts[keyword] += 1
                matched_keywords.append(keyword)

        if len(matched_keywords) > 0:
            entry = {
                'line_number': line_number,
                'text': line,
                'keywords': matched_keywords
            }
            problem_entries.append(entry)

    return problem_entries, keyword_counts


def save_problem_lines(file_name, problem_entries):
    with open(file_name, 'w', encoding='utf-8') as file:
        for entry in problem_entries:
            keyword_text = ', '.join(entry['keywords'])
            line_text = entry['text'].rstrip('\n')

            file.write('[line ' + str(entry['line_number']) + '] ')
            file.write('[keywords: ' + keyword_text + '] ')
            file.write(line_text + '\n')


def get_top_keywords(keyword_counts):
    keyword_items = []

    for keyword, count in keyword_counts.items():
        if count > 0:
            keyword_items.append((count, keyword))

    keyword_items.sort(reverse=True)

    return keyword_items[:5]


def get_group_score(keyword_counts, keywords):
    total = 0

    for keyword in keywords:
        total += keyword_counts.get(keyword, 0)

    return total


def infer_possible_cause(keyword_counts):
    pressure_score = get_group_score(
        keyword_counts,
        ['pressure', 'leak', 'low oxygen', 'oxygen']
    )
    power_score = get_group_score(
        keyword_counts,
        ['power loss', 'shutdown', 'fault']
    )
    heat_score = get_group_score(
        keyword_counts,
        ['overheat', 'temperature', 'critical']
    )
    error_score = get_group_score(
        keyword_counts,
        ['error', 'fail', 'failed', 'exception']
    )
    explosion_score = get_group_score(
        keyword_counts,
        ['explode', 'explosion']
    )

    scores = [
        ('압력 또는 산소 계통 이상 가능성', pressure_score),
        ('전력 계통 이상 가능성', power_score),
        ('과열 또는 온도 이상 가능성', heat_score),
        ('소프트웨어 또는 제어 오류 가능성', error_score),
        ('폭발 직접 징후 가능성', explosion_score)
    ]

    scores.sort(key=lambda item: item[1], reverse=True)

    if scores[0][1] == 0:
        return '문제가 되는 키워드가 명확히 검출되지 않아 단일 원인을 확정하기 어렵다.'

    return (
        '로그 키워드 기준으로는 '
        + scores[0][0]
        + '이 가장 먼저 의심된다. '
        + '다만 최종 결론은 해당 구간의 원문 로그와 전후 문맥을 함께 확인해야 한다.'
    )


def get_context_lines(lines, line_number, window_size):
    start_index = line_number - window_size - 1
    end_index = line_number + window_size

    if start_index < 0:
        start_index = 0

    if end_index > len(lines):
        end_index = len(lines)

    context_entries = []

    for index in range(start_index, end_index):
        context_entries.append((index + 1, lines[index].rstrip('\n')))

    return context_entries

def write_report(file_name, lines, problem_entries, keyword_counts):
    top_keywords = get_top_keywords(keyword_counts)
    possible_cause = infer_possible_cause(keyword_counts)

    report_lines = []

    report_lines.append('# 미션 컴퓨터 로그 분석 보고서\n\n')

    report_lines.append('## 1. 개요\n\n')
    report_lines.append('- 파일명: `mission_computer_main.log`\n')
    report_lines.append('- 총 로그 줄 수: ' + str(len(lines)) + '줄\n')
    report_lines.append(
        '- 문제 의심 로그 수: ' + str(len(problem_entries)) + '줄\n\n'
    )

    report_lines.append('## 2. 분석 방법\n\n')
    report_lines.append(
        '- 전체 로그를 UTF-8 인코딩으로 읽어 화면에 출력하였다.\n'
    )
    report_lines.append(
        '- 로그를 시간 역순으로 재정렬하여 별도 파일에 저장하였다.\n'
    )
    report_lines.append(
        '- 미리 정의한 키워드를 기준으로 이상 징후가 의심되는 로그를 1차 추출하였다.\n'
    )
    report_lines.append(
        '- 각 의심 로그에 대해 원본 파일의 행 번호를 함께 기록하여, '
        '해당 위치의 전후 문맥을 직접 다시 확인할 수 있도록 하였다.\n'
    )
    report_lines.append(
        '- 최종 원인 추정은 키워드 빈도만으로 단정하지 않고, '
        '문제 의심 로그의 전후 문맥을 함께 검토하는 방식으로 수행하였다.\n\n'
    )

    report_lines.append('## 3. 주요 키워드 집계\n\n')

    if len(top_keywords) == 0:
        report_lines.append('- 검출된 주요 키워드 없음\n\n')
    else:
        for count, keyword in top_keywords:
            report_lines.append(
                '- `' + keyword + '` : ' + str(count) + '회\n'
            )
        report_lines.append('\n')

    report_lines.append('## 4. 사고 원인 추정\n\n')
    report_lines.append(possible_cause + '\n\n')

    report_lines.append('## 5. 문제 의심 로그와 원본 위치\n\n')

    if len(problem_entries) == 0:
        report_lines.append('- 문제 의심 로그를 찾지 못했다.\n\n')
    else:
        preview_count = 5
        if len(problem_entries) < preview_count:
            preview_count = len(problem_entries)

        for index in range(preview_count):
            entry = problem_entries[index]
            line_number = entry['line_number']
            line_text = entry['text'].rstrip('\n')
            keyword_text = ', '.join(entry['keywords'])

            report_lines.append(
                '### 의심 로그 ' + str(index + 1) + '\n\n'
            )
            report_lines.append(
                '- 원본 행 번호: ' + str(line_number) + '\n'
            )
            report_lines.append(
                '- 검출 키워드: ' + keyword_text + '\n'
            )
            report_lines.append(
                '- 원본 로그: `' + line_text + '`\n\n'
            )

            report_lines.append('- 주변 문맥\n\n')
            report_lines.append('```text\n')

            context_entries = get_context_lines(lines, line_number, 1)

            for context_line_number, context_text in context_entries:
                marker = ' '
                if context_line_number == line_number:
                    marker = '*'

                report_lines.append(
                    marker
                    + ' line '
                    + str(context_line_number)
                    + ': '
                    + context_text
                    + '\n'
                )

            report_lines.append('```\n\n')

    report_lines.append('## 6. 1차 분석 결과\n\n')
    report_lines.append(
        '로그 내에서 이상 징후로 해석될 수 있는 항목들을 1차적으로 추출하였다. '
        '각 항목에 대해 원본 파일의 행 번호와 주변 문맥을 함께 제시하였으며, '
        '이를 바탕으로 이후 최종 결론을 도출할 수 있도록 정리하였다.\n\n'
    )

    report_lines.append('## 7. 결론\n\n')

    with open(file_name, 'w', encoding='utf-8') as file:
        for line in report_lines:
            file.write(line)

def main():
    print_hello()

    try:
        lines = read_log_file(LOG_FILE)

        print_log(lines)

        reverse_lines = reverse_by_time(lines)
        save_lines(REVERSE_FILE, reverse_lines)

        problem_entries, keyword_counts = collect_problem_lines(lines)
        save_problem_lines(PROBLEM_FILE, problem_entries)

        write_report(
            REPORT_FILE,
            lines,
            problem_entries,
            keyword_counts
        )

        print('\n파일 처리가 완료되었습니다.')
        print('생성 파일:')
        print('- ' + REVERSE_FILE)
        print('- ' + PROBLEM_FILE)
        print('- ' + REPORT_FILE)

    except FileNotFoundError:
        print('로그 파일을 찾을 수 없습니다: ' + LOG_FILE)
    except PermissionError:
        print('로그 파일에 접근할 권한이 없습니다.')
    except UnicodeDecodeError:
        print('로그 파일 인코딩이 UTF-8이 아닙니다.')
    except OSError as error:
        print('파일 처리 중 운영체제 오류가 발생했습니다: ' + str(error))
    except Exception as error:
        print('예상하지 못한 오류가 발생했습니다: ' + str(error))


main()