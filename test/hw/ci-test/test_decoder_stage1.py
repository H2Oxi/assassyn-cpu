from pathlib import Path


def test_decoder_stage1():
    content = Path('impl/gen_cpu/external_src/ins_decoder.sv').read_text()
    markers = ['// add', '// sub', '// and', '// or', '// xor', '// sll', '// srl', '// sra', '// sltu']
    for marker in markers:
        assert marker in content, f"Missing R-type handler comment for {marker}"
