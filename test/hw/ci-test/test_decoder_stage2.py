from pathlib import Path


def test_decoder_stage2():
    content = Path('impl/gen_cpu/external_src/ins_decoder.sv').read_text()
    markers = ['// addi', '// andi', '// ori', '// xori', '// slli', '// srli/srai']
    for marker in markers:
        assert marker in content, f"Missing I-type handler comment for {marker}"
