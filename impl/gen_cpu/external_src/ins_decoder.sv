module ins_decoder (
    input  logic [31:0] instr_in,
    output logic        decoded_valid,
    output logic        illegal,
    output logic [2:0]  instr_format,
    output logic [4:0]  rs1_addr,
    output logic [4:0]  rs2_addr,
    output logic [4:0]  rd_addr,
    output logic        rs1_used,
    output logic        rs2_used,
    output logic        rd_write_en,
    output logic        alu_en,
    output logic [3:0]  alu_op,
    output logic [1:0]  alu_in1_sel,
    output logic [1:0]  alu_in2_sel,
    output logic [2:0]  cmp_op,
    output logic        cmp_out_used,
    output logic [2:0]  adder_use,
    output logic [1:0]  add_in1_sel,
    output logic [2:0]  add_in2_sel,
    output logic        add_postproc,
    output logic [2:0]  addr_purpose,
    output logic [2:0]  wb_data_sel,
    output logic        wb_en,
    output logic        mem_read,
    output logic        mem_write,
    output logic        mem_wdata_sel,
    output logic [3:0]  mem_wstrb,
    output logic [31:0] imm_i,
    output logic [31:0] imm_s,
    output logic [31:0] imm_b,
    output logic [31:0] imm_u,
    output logic [31:0] imm_j,
    output logic [4:0]  shamt5
);

    // Instruction format encodings
    localparam logic [2:0] FMT_R        = 3'd0;
    localparam logic [2:0] FMT_I        = 3'd1;
    localparam logic [2:0] FMT_S        = 3'd2;
    localparam logic [2:0] FMT_B        = 3'd3;
    localparam logic [2:0] FMT_U        = 3'd4;
    localparam logic [2:0] FMT_J        = 3'd5;
    localparam logic [2:0] FMT_SYS      = 3'd6;
    localparam logic [2:0] FMT_ILLEGAL  = 3'd7;

    // ALU op encodings (must match impl/gen_cpu/decoder_defs.py)
    localparam logic [3:0] ALU_ADD      = 4'd0;
    localparam logic [3:0] ALU_SUB      = 4'd1;
    localparam logic [3:0] ALU_AND      = 4'd2;
    localparam logic [3:0] ALU_OR       = 4'd3;
    localparam logic [3:0] ALU_XOR      = 4'd4;
    localparam logic [3:0] ALU_SLL      = 4'd5;
    localparam logic [3:0] ALU_SRL      = 4'd6;
    localparam logic [3:0] ALU_SRA      = 4'd7;
    localparam logic [3:0] ALU_SLTU     = 4'd8;
    localparam logic [3:0] ALU_NONE     = 4'hF;

    // Comparator op encodings
    localparam logic [2:0] CMP_EQ       = 3'd0;
    localparam logic [2:0] CMP_NE       = 3'd1;
    localparam logic [2:0] CMP_LT       = 3'd2;
    localparam logic [2:0] CMP_GE       = 3'd3;
    localparam logic [2:0] CMP_LTU      = 3'd4;
    localparam logic [2:0] CMP_GEU      = 3'd5;
    localparam logic [2:0] CMP_NONE     = 3'd6;

    // ALU input selectors
    localparam logic [1:0] ALU_IN1_ZERO      = 2'd0;
    localparam logic [1:0] ALU_IN1_RS1       = 2'd1;

    localparam logic [1:0] ALU_IN2_ZERO      = 2'd0;
    localparam logic [1:0] ALU_IN2_RS2       = 2'd1;
    localparam logic [1:0] ALU_IN2_IMM_I     = 2'd2;
    localparam logic [1:0] ALU_IN2_IMM_SHAMT = 2'd3;

    // Adder usage codes
    localparam logic [2:0] ADDER_NONE        = 3'd0;
    localparam logic [2:0] ADDER_EA          = 3'd1;
    localparam logic [2:0] ADDER_PC_REL      = 3'd2;
    localparam logic [2:0] ADDER_BR_TARGET   = 3'd3;
    localparam logic [2:0] ADDER_IND_TARGET  = 3'd4;
    localparam logic [2:0] ADDER_J_TARGET    = 3'd5;

    // Adder input selectors
    localparam logic [1:0] ADD_IN1_ZERO      = 2'd0;
    localparam logic [1:0] ADD_IN1_RS1       = 2'd1;
    localparam logic [1:0] ADD_IN1_PC        = 2'd2;

    localparam logic [2:0] ADD_IN2_ZERO      = 3'd0;
    localparam logic [2:0] ADD_IN2_IMM_I     = 3'd1;
    localparam logic [2:0] ADD_IN2_IMM_S     = 3'd2;
    localparam logic [2:0] ADD_IN2_IMM_B     = 3'd3;
    localparam logic [2:0] ADD_IN2_IMM_J     = 3'd4;
    localparam logic [2:0] ADD_IN2_UIMM      = 3'd5;

    // Adder post processing
    localparam logic ADD_POST_NONE           = 1'b0;
    localparam logic ADD_POST_CLR_LSB        = 1'b1;

    // Address purpose tags
    localparam logic [2:0] ADDR_NONE         = 3'd0;
    localparam logic [2:0] ADDR_EA           = 3'd1;
    localparam logic [2:0] ADDR_BR           = 3'd2;
    localparam logic [2:0] ADDR_IND          = 3'd3;
    localparam logic [2:0] ADDR_J            = 3'd4;

    // Writeback selectors
    localparam logic [2:0] WB_NONE           = 3'd0;
    localparam logic [2:0] WB_ALU            = 3'd1;
    localparam logic [2:0] WB_IMM_LUI        = 3'd2;
    localparam logic [2:0] WB_ADDER          = 3'd3;
    localparam logic [2:0] WB_LOAD           = 3'd4;
    localparam logic [2:0] WB_LOAD_ZEXT8     = 3'd5;
    localparam logic [2:0] WB_PC_PLUS4       = 3'd6;

    // Memory write data selector
    localparam logic MEM_WDATA_NONE          = 1'b0;
    localparam logic MEM_WDATA_RS2           = 1'b1;

    // Field aliases
    wire [6:0] opcode   = instr_in[6:0];
    wire [2:0] funct3   = instr_in[14:12];
    wire [6:0] funct7   = instr_in[31:25];
    wire [11:0] imm12   = instr_in[31:20];
    wire [4:0] rs1_raw  = instr_in[19:15];
    wire [4:0] rs2_raw  = instr_in[24:20];
    wire [4:0] rd_raw   = instr_in[11:7];

    always_comb begin
        // Immediate extraction (some pre-shifted per rv32i.csv intent)
        imm_i  = {{20{instr_in[31]}}, instr_in[31:20]};
        imm_s  = {{20{instr_in[31]}}, instr_in[31:25], instr_in[11:7]};
        imm_b  = {{19{instr_in[31]}}, instr_in[31], instr_in[7], instr_in[30:25], instr_in[11:8], 1'b0};
        imm_u  = {instr_in[31:12], 12'b0};
        imm_j  = {{11{instr_in[31]}}, instr_in[31], instr_in[19:12], instr_in[20], instr_in[30:21], 1'b0};
        shamt5 = instr_in[24:20];

        // Default outputs
        decoded_valid = 1'b0;
        illegal       = 1'b1;
        instr_format  = FMT_ILLEGAL;

        rs1_addr   = rs1_raw;
        rs2_addr   = rs2_raw;
        rd_addr    = rd_raw;
        rs1_used   = 1'b0;
        rs2_used   = 1'b0;
        rd_write_en = 1'b0;

        alu_en       = 1'b0;
        alu_op       = ALU_NONE;
        alu_in1_sel  = ALU_IN1_ZERO;
        alu_in2_sel  = ALU_IN2_ZERO;
        cmp_op       = CMP_NONE;
        cmp_out_used = 1'b0;

        adder_use    = ADDER_NONE;
        add_in1_sel  = ADD_IN1_ZERO;
        add_in2_sel  = ADD_IN2_ZERO;
        add_postproc = ADD_POST_NONE;
        addr_purpose = ADDR_NONE;

        wb_data_sel = WB_NONE;
        wb_en       = 1'b0;

        mem_read      = 1'b0;
        mem_write     = 1'b0;
        mem_wdata_sel = MEM_WDATA_NONE;
        mem_wstrb     = 4'b0000;

        unique case (opcode)
            7'b0110011: begin
                bit valid_r = 1'b0;
                logic [3:0] sel_op = ALU_ADD;
                unique case ({funct7, funct3})
                    {7'b0000000, 3'b000}: begin valid_r = 1'b1; sel_op = ALU_ADD;  end // add
                    {7'b0100000, 3'b000}: begin valid_r = 1'b1; sel_op = ALU_SUB;  end // sub
                    {7'b0000000, 3'b111}: begin valid_r = 1'b1; sel_op = ALU_AND;  end // and
                    {7'b0000000, 3'b110}: begin valid_r = 1'b1; sel_op = ALU_OR;   end // or
                    {7'b0000000, 3'b100}: begin valid_r = 1'b1; sel_op = ALU_XOR;  end // xor
                    {7'b0000000, 3'b001}: begin valid_r = 1'b1; sel_op = ALU_SLL;  end // sll
                    {7'b0000000, 3'b101}: begin valid_r = 1'b1; sel_op = ALU_SRL;  end // srl
                    {7'b0100000, 3'b101}: begin valid_r = 1'b1; sel_op = ALU_SRA;  end // sra
                    {7'b0000000, 3'b011}: begin valid_r = 1'b1; sel_op = ALU_SLTU; end // sltu
                    default: begin
                        valid_r = 1'b0;
                    end
                endcase
                if (valid_r) begin
                    decoded_valid = 1'b1;
                    illegal       = 1'b0;
                    instr_format  = FMT_R;
                    rs1_used      = 1'b1;
                    rs2_used      = 1'b1;
                    rd_write_en   = 1'b1;
                    wb_en         = (rd_raw != 5'd0);
                    alu_en        = 1'b1;
                    alu_op        = sel_op;
                    alu_in1_sel   = ALU_IN1_RS1;
                    alu_in2_sel   = ALU_IN2_RS2;
                    wb_data_sel   = WB_ALU;
                end
            end

            7'b0010011: begin
                bit valid_i = 1'b0;
                logic [3:0] sel_op = ALU_ADD;
                logic [1:0] sel_in2 = ALU_IN2_IMM_I;
                unique case (funct3)
                    3'b000: begin valid_i = 1'b1; sel_op = ALU_ADD; sel_in2 = ALU_IN2_IMM_I; end // addi
                    3'b111: begin valid_i = 1'b1; sel_op = ALU_AND; sel_in2 = ALU_IN2_IMM_I; end // andi
                    3'b110: begin valid_i = 1'b1; sel_op = ALU_OR;  sel_in2 = ALU_IN2_IMM_I; end // ori
                    3'b100: begin valid_i = 1'b1; sel_op = ALU_XOR; sel_in2 = ALU_IN2_IMM_I; end // xori
                    3'b001: begin
                        if (funct7 == 7'b0000000) begin
                            valid_i = 1'b1;
                            sel_op  = ALU_SLL;
                            sel_in2 = ALU_IN2_IMM_SHAMT;
                        end
                    end // slli
                    3'b101: begin
                        if (funct7 == 7'b0000000) begin
                            valid_i = 1'b1;
                            sel_op  = ALU_SRL;
                            sel_in2 = ALU_IN2_IMM_SHAMT;
                        end else if (funct7 == 7'b0100000) begin
                            valid_i = 1'b1;
                            sel_op  = ALU_SRA;
                            sel_in2 = ALU_IN2_IMM_SHAMT;
                        end
                    end // srli/srai
                    default: begin
                        valid_i = 1'b0;
                    end
                endcase
                if (valid_i) begin
                    decoded_valid = 1'b1;
                    illegal       = 1'b0;
                    instr_format  = FMT_I;
                    rs1_used      = 1'b1;
                    rd_write_en   = 1'b1;
                    wb_en         = (rd_raw != 5'd0);
                    alu_en        = 1'b1;
                    alu_op        = sel_op;
                    alu_in1_sel   = ALU_IN1_RS1;
                    alu_in2_sel   = sel_in2;
                    wb_data_sel   = WB_ALU;
                end
            end

            7'b0110111: begin // LUI
                decoded_valid = 1'b1;
                illegal       = 1'b0;
                instr_format  = FMT_U;
                rd_write_en   = 1'b1;
                wb_en         = (rd_raw != 5'd0);
                wb_data_sel   = WB_IMM_LUI;
            end

            7'b0010111: begin // AUIPC
                decoded_valid = 1'b1;
                illegal       = 1'b0;
                instr_format  = FMT_U;
                rd_write_en   = 1'b1;
                wb_en         = (rd_raw != 5'd0);
                adder_use     = ADDER_PC_REL;
                add_in1_sel   = ADD_IN1_PC;
                add_in2_sel   = ADD_IN2_UIMM;
                addr_purpose  = ADDR_NONE;
                wb_data_sel   = WB_ADDER;
            end

            7'b0000011: begin // Loads
                bit valid_load = 1'b0;
                logic [2:0] wb_sel = WB_LOAD;
                unique case (funct3)
                    3'b010: begin valid_load = 1'b1; wb_sel = WB_LOAD;       end // lw
                    3'b100: begin valid_load = 1'b1; wb_sel = WB_LOAD_ZEXT8; end // lbu
                    default: valid_load = 1'b0;
                endcase
                if (valid_load) begin
                    decoded_valid = 1'b1;
                    illegal       = 1'b0;
                    instr_format  = FMT_I;
                    rs1_used      = 1'b1;
                    rd_write_en   = 1'b1;
                    wb_en         = (rd_raw != 5'd0);
                    adder_use     = ADDER_EA;
                    add_in1_sel   = ADD_IN1_RS1;
                    add_in2_sel   = ADD_IN2_IMM_I;
                    addr_purpose  = ADDR_EA;
                    mem_read      = 1'b1;
                    wb_data_sel   = wb_sel;
                end
            end

            7'b0100011: begin // Stores
                if (funct3 == 3'b010) begin // sw
                    decoded_valid = 1'b1;
                    illegal       = 1'b0;
                    instr_format  = FMT_S;
                    rs1_used      = 1'b1;
                    rs2_used      = 1'b1;
                    adder_use     = ADDER_EA;
                    add_in1_sel   = ADD_IN1_RS1;
                    add_in2_sel   = ADD_IN2_IMM_S;
                    addr_purpose  = ADDR_EA;
                    mem_write     = 1'b1;
                    mem_wdata_sel = MEM_WDATA_RS2;
                    mem_wstrb     = 4'hF;
                end
            end

            7'b1100011: begin // Branches
                bit valid_br = 1'b0;
                logic [2:0] sel_cmp = CMP_EQ;
                unique case (funct3)
                    3'b000: begin valid_br = 1'b1; sel_cmp = CMP_EQ;  end // beq
                    3'b001: begin valid_br = 1'b1; sel_cmp = CMP_NE;  end // bne
                    3'b100: begin valid_br = 1'b1; sel_cmp = CMP_LT;  end // blt
                    3'b101: begin valid_br = 1'b1; sel_cmp = CMP_GE;  end // bge
                    3'b110: begin valid_br = 1'b1; sel_cmp = CMP_LTU; end // bltu
                    3'b111: begin valid_br = 1'b1; sel_cmp = CMP_GEU; end // bgeu
                    default: valid_br = 1'b0;
                endcase
                if (valid_br) begin
                    decoded_valid = 1'b1;
                    illegal       = 1'b0;
                    instr_format  = FMT_B;
                    rs1_used      = 1'b1;
                    rs2_used      = 1'b1;
                    cmp_op        = sel_cmp;
                    cmp_out_used  = 1'b1;
                    adder_use     = ADDER_BR_TARGET;
                    add_in1_sel   = ADD_IN1_PC;
                    add_in2_sel   = ADD_IN2_IMM_B;
                    addr_purpose  = ADDR_BR;
                end
            end

            7'b1101111: begin // JAL
                decoded_valid = 1'b1;
                illegal       = 1'b0;
                instr_format  = FMT_J;
                rd_write_en   = 1'b1;
                wb_en         = (rd_raw != 5'd0);
                adder_use     = ADDER_J_TARGET;
                add_in1_sel   = ADD_IN1_PC;
                add_in2_sel   = ADD_IN2_IMM_J;
                addr_purpose  = ADDR_BR;
                wb_data_sel   = WB_PC_PLUS4;
            end

            7'b1100111: begin // JALR
                if (funct3 == 3'b000) begin
                    decoded_valid = 1'b1;
                    illegal       = 1'b0;
                    instr_format  = FMT_I;
                    rs1_used      = 1'b1;
                    rd_write_en   = 1'b1;
                    wb_en         = (rd_raw != 5'd0);
                    adder_use     = ADDER_IND_TARGET;
                    add_in1_sel   = ADD_IN1_RS1;
                    add_in2_sel   = ADD_IN2_IMM_I;
                    add_postproc  = ADD_POST_CLR_LSB;
                    addr_purpose  = ADDR_IND;
                    wb_data_sel   = WB_PC_PLUS4;
                end
            end

            7'b0001111: begin // FENCE
                if (funct3 == 3'b000) begin
                    decoded_valid = 1'b1;
                    illegal       = 1'b0;
                    instr_format  = FMT_SYS;
                end
            end

            7'b1110011: begin // SYSTEM
                if (funct3 == 3'b000) begin
                    if ((imm12 == 12'h000) && (rs1_raw == 5'd0) && (rd_raw == 5'd0)) begin
                        // ECALL
                        decoded_valid = 1'b1;
                        illegal       = 1'b0;
                        instr_format  = FMT_SYS;
                    end else if ((imm12 == 12'h001) && (rs1_raw == 5'd0) && (rd_raw == 5'd0)) begin
                        // EBREAK
                        decoded_valid = 1'b1;
                        illegal       = 1'b0;
                        instr_format  = FMT_SYS;
                    end else if ((imm12 == 12'h302) && (rs1_raw == 5'd0) && (rd_raw == 5'd0)) begin
                        // MRET
                        decoded_valid = 1'b1;
                        illegal       = 1'b0;
                        instr_format  = FMT_SYS;
                    end
                end
            end

            default: begin
                // Defaults already mark instruction as illegal.
            end
        endcase
    end

endmodule
