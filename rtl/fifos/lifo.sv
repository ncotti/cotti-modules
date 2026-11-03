// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026  Nicolas Gabriel Cotti

/// @brief Classic LIFO (Last In Last Out).
///
/// The value read at the output is present after a "pop" operation. E.g.:
/// rstN = 0;   (LIFO: 0x00 0x00 0x00) -> dout == 0x00
/// push 0xAA;  (LIFO: 0xAA 0x00 0x00) -> dout == 0x00
/// push 0xBB;  (LIFO: 0xAA 0xBB 0x00) -> dout == 0x00
/// pop;        (LIFO: 0xAA 0x00 0x00) -> dout == 0xBB
/// nop;        (LIFO: 0xBB 0x00 0x00) -> dout == 0xBB
/// pop;        (LIFO: 0x00 0x00 0x00) -> dout == 0xAA
///
/// @param DATA_WIDTH Number of bits in the data.
/// @param SIZE_WORDS Number of **words** to store in the LIFO.
/// @param clk Clock signal.
/// @param rstN Synchronous negative asserted reset signal.
/// @param din Data input.
/// @param push Push `din` into the LIFO. If it is full, then no value will be
/// written unless a `pop` is also issued in the same clock cycle.
/// @param pop Pop `dout` out of the LIFO. If the LIFO is empty, then this
/// operation does nothing, and `dout` does not change, unless a push is
/// also requested in the same cycle.
/// @param dout Data output.
/// @param empty Indicates that the LIFO is empty.
/// @param full Indicates that the LIFO is full.
/// @param num Indicates the number of elements currently stored in the LIFO,
/// from 0 to `SIZE_WORDS`
module lifo #(
    int DATA_WIDTH = 32,
    int SIZE_WORDS = 5
) (
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

    localparam int NumWidth = $clog2(SIZE_WORDS + 1);
    localparam int MemWidth = $clog2(SIZE_WORDS);

    logic [MemWidth-1:0] read_pointer, write_pointer;
    logic do_push, do_pop;
    logic we;
    logic [DATA_WIDTH-1:0] ram_dout, dout_reg;
    logic pop_reg, empty_reg;

    assign do_push = (push & ~full) | (push & pop);
    assign do_pop = (pop & ~empty) | (push & pop);
    assign we = rstN & do_push;

    assign full = (num == NumWidth'(SIZE_WORDS));
    assign empty = (num == '0);

    assign dout = (pop_reg & ~empty_reg) ? ram_dout : dout_reg;

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
            read_pointer <= '0;
            write_pointer <= '0;
            dout_reg <= '0;
            pop_reg <= 1'b0;
            empty_reg <= 1'b0;
        end else begin
            dout_reg  <= (push & pop & empty) ? din : dout;
            pop_reg   <= pop;
            empty_reg <= empty;

            case ({
                do_push, do_pop
            })
                2'b01: begin
                    num <= num - 1;
                    read_pointer <= read_pointer - 1;
                    write_pointer <= read_pointer;
                end
                2'b10: begin
                    num <= num + 1;
                    write_pointer <= write_pointer + 1;
                    read_pointer <= write_pointer;
                end
                2'b11: begin
                    num <= num;
                    write_pointer <= write_pointer;
                    read_pointer <= write_pointer;
                end
                default: begin
                    num <= num;
                    write_pointer <= write_pointer;
                    read_pointer <= read_pointer;
                end
            endcase
        end
    end

endmodule : lifo
