"""Shared enums and constants for the generated instruction decoder."""

from enum import IntEnum


class InstrFormat(IntEnum):
    R = 0
    I = 1
    S = 2
    B = 3
    U = 4
    J = 5
    SYS = 6
    ILLEGAL = 7


class AluOp(IntEnum):
    ADD = 0
    SUB = 1
    AND = 2
    OR = 3
    XOR = 4
    SLL = 5
    SRL = 6
    SRA = 7
    SLTU = 8
    NONE = 15


class CmpOp(IntEnum):
    EQ = 0
    NE = 1
    LT = 2
    GE = 3
    LTU = 4
    GEU = 5
    NONE = 6


class AluIn1Sel(IntEnum):
    ZERO = 0
    RS1 = 1


class AluIn2Sel(IntEnum):
    ZERO = 0
    RS2 = 1
    IMM_I = 2
    IMM_SHAMT5 = 3


class AdderUse(IntEnum):
    NONE = 0
    EA = 1
    PC_REL = 2
    BR_TARGET = 3
    IND_TARGET = 4
    J_TARGET = 5


class AddIn1Sel(IntEnum):
    ZERO = 0
    RS1 = 1
    PC = 2


class AddIn2Sel(IntEnum):
    ZERO = 0
    IMM_I = 1
    IMM_S = 2
    IMM_B_SHL1 = 3
    IMM_J_SHL1 = 4
    UIMM_SHL12 = 5


class AddPostproc(IntEnum):
    NONE = 0
    CLR_LSB = 1


class AddrPurpose(IntEnum):
    NONE = 0
    EA = 1
    BR_TARGET = 2
    IND_TARGET = 3
    J_TARGET = 4


class WbDataSel(IntEnum):
    NONE = 0
    ALU = 1
    IMM_LUI = 2
    ADDER = 3
    LOAD = 4
    LOAD_ZEXT8 = 5
    PC_PLUS4 = 6


class MemWDataSel(IntEnum):
    NONE = 0
    RS2 = 1
