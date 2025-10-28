from assassyn.frontend import *
from assassyn.test import run_test, StimulusTimeline


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


def _build_fsm_stimulus():
    timeline = StimulusTimeline(Int(32))
    timeline.signal('a', Int(32)).default(lambda cnt: cnt)
    return timeline


class Driver(Module):

    def __init__(self, timeline: StimulusTimeline):
        super().__init__(ports={})
        self.timeline = timeline

    @module.combinational
    def build(self, adder: FSM_m):
        cnt = self.timeline.build_counter()
        cnt[0] = cnt[0] + self.timeline.counter_dtype(self.timeline.step)
        values = self.timeline.values(cnt[0])
        cond = cnt[0] < Int(32)(100)
        with Condition(cond):
            adder.async_called(a=values['a'])




def test_fsm():
    def top():
        
        adder1 = FSM_m()
        adder1.build()

        timeline = _build_fsm_stimulus()
        driver = Driver(timeline)
        driver.build(adder1)

    def checker(raw):
        assert raw is not None

    run_test('FSM', top, checker,
             sim_threshold=200,
             idle_threshold=200,
             random=True)




if __name__ == '__main__':
    test_fsm()
