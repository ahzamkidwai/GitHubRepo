
from pathlib import Path

from app.parser.tree_sitter_parser import TreeSitterParser
from app.parser.symbol_extractor import SymbolExtractor


def test_python_ast_extraction():

    file_path = Path(__file__).parent / "sample_code.py"

    parser = TreeSitterParser()

    result = parser.parse_file(str(file_path))

    extractor = SymbolExtractor()

    output = extractor.extract(
        root_node=result["root_node"],
        source_bytes=result["source_bytes"],
        file_path="sample_code.py",
        language="python"
    )

    assert output["summary"]["total_functions"] == 2

    assert output["summary"]["total_classes"] == 1

    assert output["summary"]["total_imports"] == 1

    assert any(
        symbol["name"] == "calculate_total"
        for symbol in output["symbols"]
    )

    assert any(
        symbol["name"] == "PaymentService"
        for symbol in output["symbols"]
    )

    assert any(
        call["callee"] == "calculate_total"
        for call in output["calls"]
    )

    print(output)


if __name__ == "__main__":

    test_python_ast_extraction()
