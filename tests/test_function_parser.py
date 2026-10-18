from changescope.function_parser import extract_functions


def test_extracts_function_names():
    source = """
def calculate_total(price, quantity):
    return price * quantity

def process_payment(amount):
    return amount
"""
    functions = extract_functions(source)

    assert [function.name for function in functions] == [
        "calculate_total",
        "process_payment",
    ]


def test_extracts_function_line_numbers():
    source = """def first():
    pass

def second():
    pass
"""
    functions = extract_functions(source)

    assert functions[0].line_number == 1
    assert functions[1].line_number == 4


def test_extracts_async_functions():
    source = """async def fetch_data():
    return None
"""
    functions = extract_functions(source)

    assert len(functions) == 1
    assert functions[0].name == "fetch_data"


def test_invalid_python_returns_empty_list():
    source = "def broken(:"
    assert extract_functions(source) == []


def test_empty_source_returns_empty_list():
    assert extract_functions("") == []
