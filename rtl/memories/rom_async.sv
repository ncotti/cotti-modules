// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026  Nicolas Gabriel Cotti

/// @brief This is an asynchronous ROM memory, whose values are preloaded with
/// the contents of the file `ROM_FILE`. It is synthesizable.
///
/// An async ROM should be used for small LUTs (Look-up tables), and its
/// synchronous counterpart should be preferred when possible.
///
/// @param DATA_WIDTH Number of bits for each stored word.
/// @param ADDR_WIDTH_WORDS Number of bits addressing the data.
/// This parameter defines the size of the ROM, as `2^ADDR_WIDTH_WORDS`
/// **words** will be stored.
/// @param raddr Address of the data to be retrieved.
/// @param rdata Data read from `raddr`.
module rom_async #(
    int DATA_WIDTH = 8,
    int ADDR_WIDTH_WORDS = 4,
    string ROM_FILE = "tb/memories/rom_async.hex"
) (
    input logic [ADDR_WIDTH_WORDS-1:0] raddr,
    output logic [DATA_WIDTH-1:0] rdata
);

    timeunit 1ns; timeprecision 1ns;

    localparam int RomSize = 2 ** ADDR_WIDTH_WORDS;

    logic [DATA_WIDTH-1:0] rom_mem[RomSize];

    initial begin
        $readmemh(ROM_FILE, rom_mem);
    end

    assign rdata = rom_mem[raddr];

endmodule : rom_async
