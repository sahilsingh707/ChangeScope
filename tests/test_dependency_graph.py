from changescope.dependency_graph import (
    build_dependency_graph,
    find_affected_functions,
)


def test_builds_function_call_graph():
    source = """\
def calculate_total(price):
    return price * 1.18

def create_invoice(price):
    return calculate_total(price)

def send_invoice(price):
    return create_invoice(price)
"""
    graph = build_dependency_graph(source)

    assert graph["create_invoice"] == {"calculate_total"}
    assert graph["send_invoice"] == {"create_invoice"}


def test_finds_transitive_affected_functions():
    graph = {
        "create_invoice": {"calculate_total"},
        "send_invoice": {"create_invoice"},
        "log_event": set(),
    }

    affected = find_affected_functions(graph, {"calculate_total"})

    assert affected == {
        "calculate_total",
        "create_invoice",
        "send_invoice",
    }


def test_handles_invalid_python():
    assert build_dependency_graph("def broken(:") == {}
