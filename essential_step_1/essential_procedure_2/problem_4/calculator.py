from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Calculator:
    MAX_ABS_VALUE = 999999999999999
    ERROR_TEXT = 'Error'

    def __init__(self):
        self.reset()

    def reset(self):
        self.current_text = '0'
        self.current_has_percent = False
        self.tokens = []
        self.waiting_for_new_number = False
        self.result_just_shown = False
        self.fixed_expression_text = ''

    def input_number(self, number):
        if self.current_text == self.ERROR_TEXT:
            self.reset()

        if self.result_just_shown:
            self.tokens = []
            self.fixed_expression_text = ''
            self.current_text = number
            self.current_has_percent = False
            self.waiting_for_new_number = False
            self.result_just_shown = False
            self._validate_current_text()
            return

        if self.current_has_percent:
            self.tokens.append(self.make_current_token())
            self.tokens.append('×')
            self.current_text = number
            self.current_has_percent = False
            self.waiting_for_new_number = False
            self.fixed_expression_text = ''
            self._validate_current_text()
            return

        if self.waiting_for_new_number:
            self.current_text = number
            self.waiting_for_new_number = False
            self._validate_current_text()
            return

        if self.current_text == '0':
            self.current_text = number
        elif self.current_text == '-0':
            self.current_text = '-' + number
        else:
            self.current_text += number

        self._validate_current_text()

    def input_dot(self):
        if self.current_text == self.ERROR_TEXT:
            self.reset()

        if self.result_just_shown:
            self.tokens = []
            self.fixed_expression_text = ''
            self.current_text = '0.'
            self.current_has_percent = False
            self.waiting_for_new_number = False
            self.result_just_shown = False
            self._validate_current_text()
            return

        if self.current_has_percent:
            self.tokens.append(self.make_current_token())
            self.tokens.append('×')
            self.current_text = '0.'
            self.current_has_percent = False
            self.waiting_for_new_number = False
            self.fixed_expression_text = ''
            self._validate_current_text()
            return

        if self.waiting_for_new_number:
            self.current_text = '0.'
            self.waiting_for_new_number = False
            self._validate_current_text()
            return

        if self.current_text == '-0':
            self.current_text = '-0.'
            return

        if '.' not in self.current_text:
            self.current_text += '.'
            self._validate_current_text()

    def add(self):
        self._set_operator('+')

    def subtract(self):
        self._set_operator('-')

    def multiply(self):
        self._set_operator('×')

    def divide(self):
        self._set_operator('÷')

    def negative_positive(self):
        if self.current_text == self.ERROR_TEXT:
            self.reset()
            return

        if self.result_just_shown:
            self.tokens = []
            self.fixed_expression_text = ''
            self.result_just_shown = False

        if self.current_text == '0':
            self.current_text = '-0'
            return

        if self.current_text == '-0':
            self.current_text = '0'
            return

        if self.current_text.startswith('-'):
            self.current_text = self.current_text[1:]
        else:
            self.current_text = '-' + self.current_text

        self._validate_current_text()

    def percent(self):
        if self.current_text == self.ERROR_TEXT:
            return

        if self.waiting_for_new_number:
            return

        if self.result_just_shown:
            self.tokens = []
            self.fixed_expression_text = ''
            self.result_just_shown = False

        self.current_has_percent = not self.current_has_percent

    def equal(self):
        if self.current_text == self.ERROR_TEXT:
            return

        expression_tokens = self.tokens[:]

        if not self.waiting_for_new_number:
            expression_tokens.append(self.make_current_token())
        elif expression_tokens and expression_tokens[-1] in ('+', '-', '×', '÷'):
            expression_tokens = expression_tokens[:-1]

        if not expression_tokens:
            if self.current_has_percent:
                token = self.make_current_token()

                try:
                    result = self.token_to_value(token, 0.0, '×')
                    self.fixed_expression_text = self.format_token(token) + ' ='
                    self.current_text = self.format_number(result)
                    self.current_has_percent = False
                    self.result_just_shown = True
                except (ZeroDivisionError, OverflowError, ValueError):
                    self.set_error()
            return

        try:
            result = self.evaluate_expression(expression_tokens)
            self.fixed_expression_text = (
                self.format_expression(expression_tokens) + ' ='
            )
            self.current_text = self.format_number(result)
            self.current_has_percent = False
            self.tokens = []
            self.waiting_for_new_number = False
            self.result_just_shown = True
        except (ZeroDivisionError, OverflowError, ValueError, IndexError):
            self.set_error()

    def set_error(self):
        self.current_text = self.ERROR_TEXT
        self.current_has_percent = False
        self.tokens = []
        self.waiting_for_new_number = False
        self.result_just_shown = False
        self.fixed_expression_text = ''

    def _set_operator(self, operator):
        if self.current_text == self.ERROR_TEXT:
            return

        self.fixed_expression_text = ''

        if self.result_just_shown:
            self.tokens = [self.current_text]
            self.result_just_shown = False
            self.current_has_percent = False
        elif not self.waiting_for_new_number:
            self.tokens.append(self.make_current_token())

        if self.tokens:
            if self.tokens[-1] in ('+', '-', '×', '÷'):
                self.tokens[-1] = operator
            else:
                self.tokens.append(operator)
        else:
            self.tokens = ['0', operator]

        self.current_text = '0'
        self.current_has_percent = False
        self.waiting_for_new_number = True

    def precedence(self, operator):
        if operator in ('×', '÷'):
            return 2
        return 1

    def apply_top_operator(self, values, operators):
        if len(values) < 2 or not operators:
            raise ValueError

        right = values.pop()
        left = values.pop()
        operator = operators.pop()

        result = self.perform_operation(left, operator, right)
        values.append(result)

    def evaluate_expression(self, tokens):
        if not tokens:
            return 0.0

        values = []
        operators = []

        for token in tokens:
            if token in ('+', '-', '×', '÷'):
                while (
                    operators
                    and self.precedence(operators[-1])
                    >= self.precedence(token)
                ):
                    self.apply_top_operator(values, operators)

                operators.append(token)
            else:
                if token.endswith('%'):
                    previous_operator = '×'
                    left_value = 0.0

                    if operators:
                        previous_operator = operators[-1]

                    if values:
                        left_value = values[-1]

                    value = self.token_to_value(
                        token,
                        left_value,
                        previous_operator
                    )
                else:
                    value = float(token)
                    self.ensure_value_range(value)

                values.append(value)

        while operators:
            self.apply_top_operator(values, operators)

        if len(values) != 1:
            raise ValueError

        self.ensure_value_range(values[0])
        return values[0]

    def token_to_value(self, token, left_value, operator):
        if token.endswith('%'):
            number_text = token[:-1]

            if number_text in ('', '-'):
                number = 0.0
            else:
                number = float(number_text)

            if operator in ('+', '-'):
                value = left_value * number / 100
            else:
                value = number / 100

            self.ensure_value_range(value)
            return value

        value = float(token)
        self.ensure_value_range(value)
        return value

    def perform_operation(self, left, operator, right):
        if operator == '+':
            value = left + right
        elif operator == '-':
            value = left - right
        elif operator == '×':
            value = left * right
        else:
            if right == 0:
                raise ZeroDivisionError
            value = left / right

        self.ensure_value_range(value)
        return value

    def ensure_value_range(self, value):
        if value != value:
            raise ValueError

        if value == float('inf') or value == -float('inf'):
            raise OverflowError

        if abs(value) > self.MAX_ABS_VALUE:
            raise OverflowError

    def _validate_current_text(self):
        if self.current_text in ('', '-', '.', '-.'):
            return

        check_text = self.current_text

        if check_text.endswith('.'):
            check_text = check_text[:-1]

        if check_text in ('', '-'):
            return

        value = float(check_text)
        self.ensure_value_range(value)

    def make_current_token(self):
        if self.current_has_percent:
            return self.current_text + '%'
        return self.current_text

    def format_number(self, value):
        rounded_value = round(value, 6)

        if abs(rounded_value) > self.MAX_ABS_VALUE:
            raise OverflowError

        if rounded_value == 0:
            return '0'

        if int(rounded_value) == rounded_value:
            text = str(int(rounded_value))
        else:
            text = f'{rounded_value:.6f}'.rstrip('0').rstrip('.')

        if text == '-0':
            return '0'

        return text

    def format_with_commas(self, text):
        if text == self.ERROR_TEXT:
            return text

        if not text:
            return '0'

        negative = False

        if text.startswith('-'):
            negative = True
            text = text[1:]

        if '.' in text:
            integer_part, decimal_part = text.split('.', 1)
        else:
            integer_part = text
            decimal_part = ''

        if integer_part == '':
            integer_part = '0'

        reversed_digits = integer_part[::-1]
        groups = []

        for i in range(0, len(reversed_digits), 3):
            groups.append(reversed_digits[i:i + 3])

        integer_part = ','.join(group[::-1] for group in groups[::-1])

        if decimal_part != '':
            result = integer_part + '.' + decimal_part
        else:
            result = integer_part

        if negative:
            result = '-' + result

        return result

    def format_token(self, token):
        if token in ('+', '-', '×', '÷'):
            return token

        if token.endswith('%'):
            return self.format_with_commas(token[:-1]) + '%'

        return self.format_with_commas(token)

    def format_expression(self, tokens):
        formatted_tokens = []

        for token in tokens:
            formatted_tokens.append(self.format_token(token))

        return ' '.join(formatted_tokens)

    def build_expression_text(self):
        if self.fixed_expression_text:
            return self.fixed_expression_text

        display_tokens = []

        for token in self.tokens:
            display_tokens.append(self.format_token(token))

        if not self.waiting_for_new_number:
            current_token = self.make_current_token()

            if display_tokens or current_token != '0' or self.current_has_percent:
                display_tokens.append(self.format_token(current_token))

        return ' '.join(display_tokens)

    def get_display_text(self):
        shown_text = self.format_with_commas(self.current_text)

        if self.current_has_percent and self.current_text != self.ERROR_TEXT:
            shown_text += '%'

        return shown_text

    def get_expression_text(self):
        return self.build_expression_text()


class CalculatorUI(QWidget):
    def __init__(self):
        super().__init__()

        self.calculator = Calculator()

        self.setWindowTitle('Calculator')
        self.setFixedSize(390, 700)
        self.setStyleSheet('background-color: black;')

        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        display_layout = QVBoxLayout()
        display_layout.setSpacing(0)

        self.expression_label = QLabel('')
        self.expression_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.expression_label.setFixedHeight(50)
        self.expression_label.setStyleSheet(
            '''
            QLabel {
                color: #aaaaaa;
                background-color: black;
                padding: 0 10px;
            }
            '''
        )

        self.display_label = QLabel('0')
        self.display_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.display_label.setFixedHeight(130)
        self.display_label.setStyleSheet(
            '''
            QLabel {
                color: white;
                background-color: black;
                padding: 0 10px 20px 10px;
            }
            '''
        )

        display_layout.addWidget(self.expression_label)
        display_layout.addWidget(self.display_label)
        main_layout.addLayout(display_layout)

        grid = QGridLayout()
        grid.setSpacing(12)

        buttons = [
            ('AC', 0, 0, 1, 1, 'top'),
            ('+/-', 0, 1, 1, 1, 'top'),
            ('%', 0, 2, 1, 1, 'top'),
            ('÷', 0, 3, 1, 1, 'operator'),
            ('7', 1, 0, 1, 1, 'number'),
            ('8', 1, 1, 1, 1, 'number'),
            ('9', 1, 2, 1, 1, 'number'),
            ('×', 1, 3, 1, 1, 'operator'),
            ('4', 2, 0, 1, 1, 'number'),
            ('5', 2, 1, 1, 1, 'number'),
            ('6', 2, 2, 1, 1, 'number'),
            ('-', 2, 3, 1, 1, 'operator'),
            ('1', 3, 0, 1, 1, 'number'),
            ('2', 3, 1, 1, 1, 'number'),
            ('3', 3, 2, 1, 1, 'number'),
            ('+', 3, 3, 1, 1, 'operator'),
            ('0', 4, 0, 1, 2, 'zero'),
            ('.', 4, 2, 1, 1, 'number'),
            ('=', 4, 3, 1, 1, 'operator'),
        ]

        for text, row, col, row_span, col_span, kind in buttons:
            button = QPushButton(text)
            button.clicked.connect(
                lambda checked, value=text: self.handle_button(value)
            )

            if kind == 'zero':
                button.setFixedSize(172, 80)
            else:
                button.setFixedSize(80, 80)

            button.setFont(QFont('Arial', 22))
            button.setStyleSheet(self.button_style(kind))
            grid.addWidget(button, row, col, row_span, col_span)

        main_layout.addLayout(grid)
        self.setLayout(main_layout)

    def button_style(self, kind):
        if kind == 'top':
            return '''
                QPushButton {
                    background-color: #a5a5a5;
                    color: black;
                    border: none;
                    border-radius: 40px;
                }
                QPushButton:pressed {
                    background-color: #c5c5c5;
                }
            '''

        if kind == 'operator':
            return '''
                QPushButton {
                    background-color: #ff9f0a;
                    color: white;
                    border: none;
                    border-radius: 40px;
                }
                QPushButton:pressed {
                    background-color: #ffb340;
                }
            '''

        if kind == 'zero':
            return '''
                QPushButton {
                    background-color: #333333;
                    color: white;
                    border: none;
                    border-radius: 40px;
                    text-align: left;
                    padding-left: 30px;
                }
                QPushButton:pressed {
                    background-color: #4a4a4a;
                }
            '''

        return '''
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                border-radius: 40px;
            }
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
        '''

    def handle_button(self, value):
        try:
            if value.isdigit():
                self.calculator.input_number(value)
            elif value == '.':
                self.calculator.input_dot()
            elif value == '+':
                self.calculator.add()
            elif value == '-':
                self.calculator.subtract()
            elif value == '×':
                self.calculator.multiply()
            elif value == '÷':
                self.calculator.divide()
            elif value == '=':
                self.calculator.equal()
            elif value == 'AC':
                self.calculator.reset()
            elif value == '+/-':
                self.calculator.negative_positive()
            elif value == '%':
                self.calculator.percent()
        except (OverflowError, ValueError):
            self.calculator.set_error()

        self.update_display()

    def update_display(self):
        shown_text = self.calculator.get_display_text()
        expression = self.calculator.get_expression_text()

        length = len(shown_text)

        if length <= 9:
            size = 48
        elif length <= 12:
            size = 38
        elif length <= 15:
            size = 30
        else:
            size = 24

        self.expression_label.setFont(QFont('Arial', 18))
        self.display_label.setFont(QFont('Arial', size))

        self.expression_label.setText(expression)
        self.display_label.setText(shown_text)


if __name__ == '__main__':
    app = QApplication([])
    window = CalculatorUI()
    window.show()
    app.exec_()