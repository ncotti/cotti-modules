// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026  Nicolas Gabriel Cotti

/// @brief Simple Dual Port Synchronous RAM (SDP_RAM).
///
/// The RAM has two ports, one for reading and other for writing, allowing
/// simultaneous reads and writes.
/// It only returns the value from the read address.
///
/// The `DATA_WIDTH` and `DATA_LANE_WIDTH` determine how the memory will be
/// written. For example, a typical configuration would be:
///     `DATA_WIDTH = 32`, `DATA_LANE_WIDTH = 8`
/// Each word has 32 bits, and the data can be written per byte, by using the
/// `we` signal, one bit per byte.
///
/// @param DATA_WIDTH Number of bits per data **word**.
/// @param DATA_LANE_WIDTH Number of bits per data lane. Each word is divided
/// in "lanes", and each lane may be individually written by setting the
/// `we` input bits.
/// `DATA_WIDTH` must be divisible by `DATA_LANE_WIDTH`.
/// @param ADDR_WIDTH_WORDS Number of bits addressing the data.
/// This parameter defines the size of the RAM, as `2^ADDR_WIDTH_WORDS`
/// **words** will be stored, each word having `DATA_WIDTH` bits.
/// @param clk Clock signal
/// @param raddr Address of the word to be read.
/// @param waddr Address of the word to be written.
/// @param we Write enable.
/// @param wdata Word to be written. A word is divided into
/// `DATA_WIDTH / DATA_LANE_WIDTH` lanes, and `we`
/// determines the lane positions that should be updated when the RAM is written.
/// E.g., for `DATA_WIDTH = 32` and `DATA_LANE_WIDTH = 8`,
/// given the address `addr = 0x0100`, which holds the value `0xDDCCBBAA`,
/// and let `wdata = 0x12345678` and `we = 4'b1011`, the word at 0x0100
/// would be set to `0x12CC5678`, i.e., the fourth, second and first  bit will
/// be written.
/// @param rdata Data read from `raddr`.
module ram_simple_dual_port #(
    int DATA_WIDTH = 16,
    int DATA_LANE_WIDTH = 8,
    int ADDR_WIDTH_WORDS = 3
) (
    input logic clk,
    input logic [ADDR_WIDTH_WORDS-1:0] raddr,
    input logic [ADDR_WIDTH_WORDS-1:0] waddr,
    input logic [(DATA_WIDTH / DATA_LANE_WIDTH) -1:0] we,
    input logic [DATA_WIDTH-1:0] wdata,
    output logic [DATA_WIDTH-1:0] rdata
);

    timeunit 1ns; timeprecision 1ns;

    initial begin
        assert ((DATA_WIDTH % DATA_LANE_WIDTH) == 0)
        else $error("DATA_WIDTH must be divisble by DATA_LANE_WIDTH");
    end

    localparam int Lanes   = DATA_WIDTH / DATA_LANE_WIDTH;
    localparam int RamSize = 2 ** ADDR_WIDTH_WORDS;

    logic [DATA_WIDTH-1:0] ram_mem[RamSize];

    always_ff @(posedge clk) begin
        rdata <= ram_mem[raddr];

        for (int i = 0; i < Lanes; i = i + 1) begin
            if (we[i]) begin
                ram_mem[waddr][i*DATA_LANE_WIDTH +: DATA_LANE_WIDTH] <=
                    wdata[i*DATA_LANE_WIDTH +: DATA_LANE_WIDTH];
            end
        end
    end

endmodule : ram_simple_dual_port
