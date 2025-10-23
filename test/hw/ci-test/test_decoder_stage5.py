from pathlib import Path


def test_decoder_stage5():
    content = Path('impl/gen_cpu/external_src/ins_decoder.sv').read_text()
    markers = ['// LUI', '// AUIPC', '// FENCE', '// ECALL', '// EBREAK', '// MRET']
    for marker in markers:
        assert marker in content, f"Missing system/U-type handler comment for {marker}"
