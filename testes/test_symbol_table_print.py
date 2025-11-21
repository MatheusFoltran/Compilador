import io
from contextlib import redirect_stdout
from interpreter import SemanticAnalyzer


def _render_symbol_table_with_sample_data() -> str:
    analyzer = SemanticAnalyzer()
    table = analyzer.symbol_table

    # Global symbol
    table.declare('global_int', 'var', 'integer')

    # Archived scope with params + locals
    table.enter_scope(owner='ProcExample', category='proc')
    table.declare('param_a', 'var', 'integer', is_param=True)
    table.declare('local_flag', 'var', 'boolean')
    table.exit_scope()

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        analyzer.print_symbol_table()
    return buffer.getvalue()


def test_symbol_table_print_includes_archived_scope_name():
    output = _render_symbol_table_with_sample_data()
    assert 'ProcExample' in output
    assert 'status=archived' in output


def test_symbol_table_print_is_ascii():
    output = _render_symbol_table_with_sample_data()
    assert output.isascii(), 'Symbol table output must be ASCII-only'
