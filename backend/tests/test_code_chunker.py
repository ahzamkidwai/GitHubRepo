from app.chunking.code_chunker import CodeChunker


def test_small_function_creates_one_chunk():

    chunker = CodeChunker(
        max_tokens=1200,
        overlap_tokens=120
    )

    symbol = {
        "symbol_id": "symbol_001",
        "name": "calculate_total",
        "qualified_name": "calculate_total",
        "symbol_type": "function",
        "file_path": "payment.py",
        "language": "python",
        "start_line": 1,
        "end_line": 3,
        "parameters": ["price", "quantity"],
        "base_classes": [],
        "code": (
            "def calculate_total(price, quantity):\n"
            "    total = price * quantity\n"
            "    return total"
        )
    }

    chunks = chunker.create_symbol_chunks(symbol)

    assert len(chunks) == 1
    assert chunks[0]["name"] == "calculate_total"
    assert chunks[0]["chunk_type"] == "function"
    assert chunks[0]["file_path"] == "payment.py"


def test_method_preserves_class_context():

    chunker = CodeChunker()

    symbol = {
        "symbol_id": "symbol_002",
        "name": "process_payment",
        "qualified_name": "PaymentService.process_payment",
        "symbol_type": "method",
        "parent_symbol": "PaymentService",
        "file_path": "payment.py",
        "language": "python",
        "start_line": 5,
        "end_line": 8,
        "parameters": ["self", "amount"],
        "base_classes": [],
        "code": (
            "def process_payment(self, amount):\n"
            "    if amount > 0:\n"
            "        return 'Success'\n"
            "    return 'Invalid'"
        )
    }

    chunks = chunker.create_symbol_chunks(
        symbol,
        class_context="class PaymentService"
    )

    assert len(chunks) == 1
    assert "class PaymentService" in chunks[0]["code"]
    assert "process_payment" in chunks[0]["code"]
    assert chunks[0]["parent_symbol"] == "PaymentService"


def test_large_code_is_split():

    chunker = CodeChunker(
        max_tokens=100,
        overlap_tokens=10
    )

    code = "\n".join(
        [f"    result_{i} = value_{i} * 100" for i in range(100)]
    )

    parts = chunker.split_code(code)

    assert len(parts) > 1
    assert all(part["code"] for part in parts)