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



def test_repository_graph_distinguishes_same_named_functions():
    from changescope.dependency_graph import build_repository_dependency_graph

    graph = build_repository_dependency_graph(
        {
            "billing.py": (
                "def process_data():\n"
                "    return 1\n\n"
                "def create_invoice():\n"
                "    return process_data()\n"
            ),
            "analytics.py": (
                "def process_data():\n"
                "    return 2\n\n"
                "def build_dashboard():\n"
                "    return process_data()\n"
            ),
        }
    )

    assert graph["billing.py::create_invoice"] == {
        "billing.py::process_data"
    }
    assert graph["analytics.py::build_dashboard"] == {
        "analytics.py::process_data"
    }


def test_repository_graph_resolves_unique_cross_file_calls():
    from changescope.dependency_graph import build_repository_dependency_graph

    graph = build_repository_dependency_graph(
        {
            "billing.py": (
                "def calculate_total():\n"
                "    return 100\n"
            ),
            "api.py": (
                "def create_invoice():\n"
                "    return calculate_total()\n"
            ),
        }
    )

    assert graph["api.py::create_invoice"] == {
        "billing.py::calculate_total"
    }




def test_detects_attribute_function_calls():
    source = """\
class Invoice:
    def create(self):
        self.validate()
        validator.calculate_total()

    def validate(self):
        return True
"""
    graph = build_dependency_graph(source)

    assert graph["Invoice.create"] == {"validate", "calculate_total"}
    assert graph["Invoice.validate"] == set()
    assert "create" not in graph
    assert "validate" not in graph

def test_repository_graph_resolves_same_file_attribute_calls():
    from changescope.dependency_graph import build_repository_dependency_graph

    graph = build_repository_dependency_graph(
        {
            "billing.py": (
                "class Invoice:\n"
                "    def create(self):\n"
                "        self.validate()\n\n"
                "    def validate(self):\n"
                "        return True\n"
            ),
        }
    )

    assert graph["billing.py::Invoice.create"] == {
        "billing.py::Invoice.validate"
    }





def test_repository_graph_distinguishes_methods_in_different_classes():
    from changescope.dependency_graph import build_repository_dependency_graph

    graph = build_repository_dependency_graph(
        {
            "billing.py": (
                "class Invoice:\n"
                "    def validate(self):\n"
                "        return True\n\n"
                "    def create(self):\n"
                "        self.validate()\n\n"
                "class Payment:\n"
                "    def validate(self):\n"
                "        return False\n\n"
                "    def process(self):\n"
                "        self.validate()\n"
            ),
        }
    )

    assert graph["billing.py::Invoice.create"] == {
        "billing.py::Invoice.validate"
    }
    assert graph["billing.py::Payment.process"] == {
        "billing.py::Payment.validate"
    }
