// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026  Nicolas Gabriel Cotti

/// @brief First Word Fall Through (FWFT) FIFO (First In First Out).
///
/// The value written is shown at the output in the next clock cycle, and the
/// "pop" operation works as a "confirmation" that the value was read, and
/// then shows the next one. It is also called a "look-ahead" FIFO
/// or "peek" FIFO. E.g.:
/// rstN = 0;   (FIFO: 0x00 0x00 0x00) -> dout == 0x00
/// push 0xAA;  (FIFO: 0xAA 0x00 0x00) -> dout == 0xAA
/// push 0xBB;  (FIFO: 0xAA 0xBB 0x00) -> dout == 0xAA
/// pop;        (FIFO: 0xBB 0x00 0x00) -> dout == 0xBB
/// nop;        (FIFO: 0xBB 0x00 0x00) -> dout == 0xBB
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
module fifo_fwft #(
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
    output logic [$clog2(SIZE_WORDS+1)-1:0] num
);

    timeunit 1ns; timeprecision 1ns;

    localparam int NumWidth = $clog2(SIZE_WORDS+1);
    localparam int MemWidth = $clog2(SIZE_WORDS);

    logic [MemWidth-1:0] read_pointer, write_pointer;
    logic do_push, do_pop;
    logic we;
    logic [DATA_WIDTH-1:0] ram_dout, dout_reg;
    logic pop_reg;
    logic bypass, bypass_reg;

    assign do_push = (push & ~full) | (push & pop);
    assign do_pop = (pop & ~empty) | (push & pop);
    assign bypass = push & pop & (num == NumWidth'(1));
    assign we = (rstN & do_push);

    assign full = (num == NumWidth'(SIZE_WORDS));
    assign empty = (num == 'd0);

    assign dout = (pop_reg & ~empty & ~bypass_reg) ? ram_dout : dout_reg;

    ram_simple_dual_port #(
        .DATA_WIDTH(DATA_WIDTH),
        .DATA_LANE_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH_WORDS(MemWidth)
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
            read_pointer <= 'd1;
            write_pointer <= '0;
            dout_reg <= '0;
            pop_reg <= 1'b0;
            bypass_reg <= 1'b0;
        end else begin
            dout_reg <= ((push & empty) | bypass ) ? din : dout;
            pop_reg <= pop;
            bypass_reg <= bypass;

            case ({do_push, do_pop})
                2'b01: num <= num - 1;
                2'b10: num <= num + 1;
                default: num <= num;
            endcase

            write_pointer <= (do_push) ? write_pointer + 1 : write_pointer;
            read_pointer <= (do_pop) ? read_pointer + 1 : read_pointer;
        end
    end

endmodule: fifo_fwft
