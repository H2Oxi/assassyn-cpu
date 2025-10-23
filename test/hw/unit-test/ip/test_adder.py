from assassyn.frontend import *
from assassyn.test import run_test
from impl.ip.ips import Adder as ExternalAdder


from assassyn.backend import elaborate
from assassyn import utils


class Driver(Module):

    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, forward1: Module, forward2: Module):
        cnt = RegArray(UInt(32), 1)
        cnt[0] = cnt[0] + UInt(32)(1)
        add_in1 = cnt[0].case({
            UInt(32)(0): Int(32)(-100).bitcast(UInt(32)),
            UInt(32)(1): Int(32)(0).bitcast(UInt(32)),
            UInt(32)(2): Int(32)(100).bitcast(UInt(32)),
            None: cnt[0],
        })
        add_in2 = cnt[0].case({
            UInt(32)(0): Int(32)(100).bitcast(UInt(32)),
            UInt(32)(1): Int(32)(-100).bitcast(UInt(32)),
            UInt(32)(2): Int(32)(-1).bitcast(UInt(32)),
            None: cnt[0],
        })

        forward1.async_called(data=add_in1)
        forward2.async_called(data=add_in2)


class ForwardData(Module):
    def __init__(self):
        super().__init__(
            ports={'data': Port(UInt(32))},
        )

    @module.combinational
    def build(self):
        data = self.pop_all_ports(True)
        return data


class Adder(Downstream):

    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self, add_in1: Value, add_in2: Value):
        #here we assumed user explicitly know the direction of the external module ports
        add_in1 = add_in1.optional(UInt(32)(1))
        add_in2 = add_in2.optional(UInt(32)(1))

        adder = ExternalAdder(add_in1=add_in1, add_in2=add_in2)
        log("[test] add_in1:{}|add_in2:{}|add_out:{}", add_in1, add_in2, adder.add_out)

def ref_model(add_in1, add_in2):
    return (add_in1 + add_in2) & 0xFFFFFFFF

def check_raw(raw):
    cnt = 0
    for i in raw.split('\n'):
        if '[test]' in i:
            line_toks = i.split('|')
            add_in1 = line_toks[0].split(':')[-1]
            add_in2 = line_toks[1].split(':')[-1]
            add_out = line_toks[2].split(':')[-1]
            ref_out = ref_model(int(add_in1), int(add_in2))
            assert int(add_out) == int(ref_out), f'Adder output incorrect: {add_in1} + {add_in2} != {ref_out}'
            cnt += 1
    assert cnt == 99, f'cnt: {cnt} != 99'

def build_system():
    driver = Driver()
    forward1 = ForwardData()
    forward2 = ForwardData()
    add_in1 = forward1.build()
    add_in2 = forward2.build()
    adder = Adder()
    driver.build(forward1, forward2)
    adder.build(add_in1, add_in2)

def test_easy_external():
    run_test('test_adder', build_system, check_raw, sim_threshold=100, idle_threshold=100)

if __name__ == '__main__':
    test_easy_external()


