/// @brief Single Port Synchronous RAM (SP_RAM).
///
/// The RAM only has one port, which can either be read and written in the
/// same cycle.
///
/// Data width is fixed at 32-bits (4-byte words), the 2 LSB bits are discarded.
/// E.g., accessing a non-aligned address like 0x8000_00XX will result in the
/// address 0x8000_0000 instead, no matter the value of "XX".
///
/// @param ADDR_WIDTH_BYTES Number of bits addressing the data.
/// This parameter defines the size of the RAM, as `2^ADDR_WIDTH_BYTES`
/// **bytes** will be stored.
/// @param clk Clock signal
/// @param addr Address to be read or written. The 2 LSB bits are discarded,
/// since addresses are 4-byte aligned.
/// @param we Write enable.
/// @param wdata Data to be written. `wdata` should be aligned to match a 4-byte
/// representation.
/// E.g, if you want to write the byte at address 0x0101 with `wstrb = 4'b0010`,
/// then the second byte of the `wdata = 0x0000XX00` should hold that value.
/// @param wstrb Write strobe. A word is divided in 4 bytes, and `wstrb`
/// determines the byte-positions that should be updated when the RAM is written.
/// E.g., given the address `0x01XX == 0x0100`, which holds the value `0xDDCCBBAA`,
/// and let `wdata = 0x12345678` and `wstrb = 4'b1011`, the memory at 0x0100
/// would be set to `12CC5678`, i.e., bytes 0x103, 0x101 and 0x100 will be written.
/// @param rdata Data read from `addr`. If a write operation was issued, then
/// the previously held value is returned, not the one being written.
/// If an unaligned memory address was specified, e.g., 0x102, the returned
/// value will be the value from 0x100, and the user should read the third
/// byte from `rdata`.
module ram_single_port #(
    int ADDR_WIDTH_BYTES = 5
) (
    input logic clk,
    input logic [ADDR_WIDTH_BYTES-1:0] addr,
    input logic we,
    input logic [31:0] wdata,
    input logic [3:0] wstrb,
    output logic [31:0] rdata
);

    timeunit 1ns; timeprecision 1ns;

    localparam int RamSize = 2 ** (ADDR_WIDTH_BYTES-2);

    logic [31:0] ram_mem[RamSize];
    logic [ADDR_WIDTH_BYTES-1:2] ram_addr;

    assign ram_addr = addr[ADDR_WIDTH_BYTES-1:2];

    always_ff @(posedge clk) begin
        rdata <= ram_mem[ram_addr];

        if (we) begin
            for (int i=0; i < 4; i=i+1) begin
                if (wstrb[i]) begin
                    ram_mem[ram_addr][i*8 +: 8] <= wdata[i*8 +: 8];
                end
            end
        end
    end

    // Use unused signals to prevent warnings
    logic _unused_ok;
    assign _unused_ok = & addr[1:0];

endmodule : ram_single_port
