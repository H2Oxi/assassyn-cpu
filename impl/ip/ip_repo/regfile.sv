// RV32I Register File Module
// 32 general-purpose registers with 2 read ports (rs1, rs2) and 1 write port (rd)
// Synchronous read/write (FPGA BRAM-friendly) with 1-cycle read latency
// Features: x0 hardwired to 0, internal bypass for read-write conflicts

module regfile(
    input  logic        clk,        // Clock signal
    input  logic        rst,        // Active-high reset
    // Read port 1 (rs1)
    input  logic [4:0]  rs1_addr,   // Read address for rs1
    output logic [31:0] rs1_data,   // Read data from rs1 (1-cycle delayed)
    // Read port 2 (rs2)
    input  logic [4:0]  rs2_addr,   // Read address for rs2
    output logic [31:0] rs2_data,   // Read data from rs2 (1-cycle delayed)
    // Write port (rd)
    input  logic        rd_we,      // Write enable
    input  logic [4:0]  rd_addr,    // Write address for rd
    input  logic [31:0] rd_wdata    // Write data for rd
);

    // Convert active-high reset to active-low for internal use
    logic rst_n;
    assign rst_n = ~rst;

    // 32 x 32-bit register file storage (BRAM-friendly)
    logic [31:0] registers [0:31];

    // Internal registers for storing read addresses (for bypass detection)
    logic [4:0] rs1_addr_reg;
    logic [4:0] rs2_addr_reg;

    // Synchronous write: write on rising edge of clock
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all registers to 0
            for (int i = 0; i < 32; i++) begin
                registers[i] <= 32'b0;
            end
        end else begin
            // Write to register if write enable is high and address is not x0
            if (rd_we && rd_addr != 5'b0) begin
                registers[rd_addr] <= rd_wdata;
            end
        end
    end

    // Synchronous read: read on rising edge of clock (1-cycle latency)
    // Store the read addresses for bypass logic
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rs1_addr_reg <= 5'b0;
            rs2_addr_reg <= 5'b0;
        end else begin
            rs1_addr_reg <= rs1_addr;
            rs2_addr_reg <= rs2_addr;
        end
    end

    // Read data output with bypass logic
    // Bypass: if writing to the same register being read in the same cycle,
    // forward the write data to the read output
    always_comb begin
        // Read port 1 (rs1)
        if (rs1_addr_reg == 5'b0) begin
            // x0 always reads as 0
            rs1_data = 32'b0;
        end else if (rd_we && rd_addr == rs1_addr_reg && rd_addr != 5'b0) begin
            // Bypass: forward write data if writing to the same register
            rs1_data = rd_wdata;
        end else begin
            // Normal read from register file
            rs1_data = registers[rs1_addr_reg];
        end

        // Read port 2 (rs2)
        if (rs2_addr_reg == 5'b0) begin
            // x0 always reads as 0
            rs2_data = 32'b0;
        end else if (rd_we && rd_addr == rs2_addr_reg && rd_addr != 5'b0) begin
            // Bypass: forward write data if writing to the same register
            rs2_data = rd_wdata;
        end else begin
            // Normal read from register file
            rs2_data = registers[rs2_addr_reg];
        end
    end

endmodule
