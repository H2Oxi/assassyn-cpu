from assassyn.frontend import *
from impl.ip.ips import RegFile

class regfile_wrapper(Downstream):
    def __init__(self, regfile: Module):
        super().__init__()
        self.regfile = regfile

    @downstream.combinational
    def build(self, rs1_addr:Value, rs2_addr:Value, rd_write_en:Value, rd_addr:Value, rd_wdata:Value):
        
        regfile = RegFile(
            rs1_addr=rs1_addr,
            rs2_addr=rs2_addr,
            rd_we   =rd_write_en,
            rd_addr =rd_addr,
            rd_wdata=rd_wdata
        )

        return regfile.rs1_data, regfile.rs2_data

