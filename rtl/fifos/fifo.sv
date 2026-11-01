/// @brief Classic FIFO (First In First Out).
///
/// The value read at the output is present after a "pop" operation. E.g.:
/// rstN = 0;   (FIFO: 0x00 0x00 0x00) -> dout == 0x00
/// push 0xAA;  (FIFO: 0xAA 0x00 0x00) -> dout == 0x00
/// push 0xBB;  (FIFO: 0xAA 0xBB 0x00) -> dout == 0x00
/// pop;        (FIFO: 0xBB 0x00 0x00) -> dout == 0xAA
/// nop;        (FIFO: 0xBB 0x00 0x00) -> dout == 0xAA
/// pop;        (FIFO: 0x00 0x00 0x00) -> dout == 0xBB
///
/// @param DATA_WIDTH Number of bits in the data.
/// @param SIZE_WORDS Number of **words** to store in the FIFO.
/// @param clk Clock signal.
/// @param rstN Synchronous negative asserted reset signal.
/// @param din Data input.
/// @param push Push `din` into the FIFO. If it is full, then no value will be
/// written unless a `pop` is also issued in the same clock cycle.
/// @param pop Pop `dout` out of the FIFO. If the FIFO is empty, then this
/// operation does nothing, and `dout` does not change.
/// @param dout Data output.
/// @param empty Indicates that the FIFO is empty.
/// @param full Indicates that the FIFO is full.
/// @param num Indicates the number of elements currently stored in the FIFO,
/// from 0 to `SIZE_WORDS`
module fifo #(
    int DATA_WIDTH = 32,
    int SIZE_WORDS = 4
)(
    input logic clk,
    input logic rstN,
    input logic [DATA_WIDTH-1:0] din,
    input logic push,
    input logic pop,
    output logic [DATA_WIDTH-1:0] dout,
    output logic empty,
    output logic full,
    output logic [$clog2(SIZE_WORDS):0] num
);

    timeunit 1ns; timeprecision 1ns;

    localparam int NumWidth = $clog2(SIZE_WORDS);

    logic [NumWidth-1:0] read_pointer, write_pointer;
    logic we;
    logic [DATA_WIDTH-1:0] ram_dout, prev_dout;
    logic pop_reg, empty_reg;

    assign full = num[NumWidth];
    assign empty = (num == '0);
    assign we = (rstN & ((push & ~pop & ~full) | (push & pop)));
    assign dout = (pop_reg & ~empty_reg) ? ram_dout : prev_dout;

    ram_simple_dual_port #(
        .DATA_WIDTH(DATA_WIDTH),
        .DATA_LANE_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH_WORDS(NumWidth)
    ) ram_i (
        .clk(clk),
        .raddr(read_pointer),
        .waddr(write_pointer),
        .we(we),
        .wdata(din),
        .wstrb(1'b1),
        .rdata(ram_dout)
    );

    always_ff @(posedge clk) begin
        if (!rstN) begin
            num <= '0;
            read_pointer <= '0;
            write_pointer <= '0;
            prev_dout <= '0;
            pop_reg <= 1'b0;
            empty_reg <= 1'b0;
        end else begin
            prev_dout <= dout;
            pop_reg <= pop;
            empty_reg <= empty;
            unique case ({push, pop})
                2'b00: begin
                    num <= num;
                    read_pointer <= read_pointer;
                    write_pointer <= write_pointer;
                end
                2'b01: begin
                    if (empty) begin
                        num <= num;
                        read_pointer <= read_pointer;
                    end else begin
                        num <= num - 1;
                        read_pointer <= read_pointer + 1;
                    end
                    write_pointer <= write_pointer;
                end
                2'b10: begin
                    if (full) begin
                        num <= num;
                        write_pointer <= write_pointer;
                    end else begin
                        num <= num + 1;
                        write_pointer <= write_pointer + 1;
                    end
                    read_pointer <= read_pointer;
                end
                2'b11: begin
                    if (empty) begin
                        read_pointer <= read_pointer;
                        num <= num + 1;
                    end else begin
                        read_pointer <= read_pointer + 1;
                        num <= num;
                    end
                    write_pointer <= write_pointer + 1;
                end
            endcase
        end
    end

endmodule: fifo
