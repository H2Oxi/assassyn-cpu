from pathlib import Path


def test_decoder_stage3():
    content = Path('impl/gen_cpu/external_src/ins_decoder.sv').read_text()
    markers = ['// lw', '// lbu', '// sw']
    for marker in markers:
        assert marker in content, f"Missing memory access handler comment for {marker}"
