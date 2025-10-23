from pathlib import Path


def test_decoder_stage4():
    content = Path('impl/gen_cpu/external_src/ins_decoder.sv').read_text()
    markers = ['// beq', '// bne', '// blt', '// bge', '// bltu', '// bgeu', '// JAL', '// JALR']
    for marker in markers:
        assert marker in content, f"Missing control-flow handler comment for {marker}"
