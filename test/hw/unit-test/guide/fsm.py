from assassyn.frontend import *
from assassyn.test import run_test


class FSM_m(Module):

    def __init__(self):
        super().__init__(
            ports={
                'a': Port(Int(32)),
            },
        )

    @module.combinational
    def build(self):
        a= self.pop_all_ports(True)
        user_state = RegArray(Bits(2), 1 , initializer=[0])

        temp = RegArray(Int(32), 1)

        cond_default = Bits(1)(1)
        cond1 = a[0:1] == UInt(2)(0)

        # define the state transition table
        transfer_table = {
            "s0": {cond_default: "s1"},
            "s1": {cond1:"s2"},
            "s2": {cond_default: "s3"},
            "s3": {cond_default: "s0"},
        }

        # define the state body functions
        def s0_body():
            (temp & self)[0] <= a
        def s3_body():
            (temp & self)[0] <= (temp[0] * Int(32)(2)).bitcast(Int(32))
        body_table = {
            "s0": s0_body,
            "s3": s3_body,
        }
        my_fsm = fsm.FSM(user_state, transfer_table)
        my_fsm.generate(body_table)


        log("state: {} | a: {} |  temp: {}  ", user_state[0] , a , temp[0])


class Driver(Module):

    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, adder: FSM_m):

        cnt = RegArray(Int(32), 1)
        cnt[0] = cnt[0] + Int(32)(1)
        cond = cnt[0] < Int(32)(100)
        with Condition(cond):
            adder.async_called(a = cnt[0])




def test_fsm():
    def top():
        
        adder1 = FSM_m()
        adder1.build()

        driver = Driver()
        driver.build(adder1)

    def checker(raw):
        assert raw is not None

    run_test('FSM', top, checker,
             sim_threshold=200,
             idle_threshold=200,
             random=True)




if __name__ == '__main__':
    test_fsm()
