/// @brief This is an asynchronous ROM memory, whose values are preloaded with
/// the contents of the file `ROM_FILE`. It is synthesizable.
///
/// An async ROM should be used for small LUTs (Look-up tables), and its
/// synchronous counterpart should be preferred when possible.
///
/// @param DATA_WIDTH Number of bits for each stored word.
/// @param ADDR_WIDTH_WORDS Number of bits addressing the data.
/// This parameter defines the size of the ROM, as `2^ADDR_WIDTH` **words**
/// will be stored.
/// @param addr Address of the data to be retrieved.
/// @param dread Data read from `addr`.
module rom_async #(
    int DATA_WIDTH = 8,
    int ADDR_WIDTH_WORDS = 4,
    string ROM_FILE = "tb/memories/rom_async.hex"
) (
    input logic [ADDR_WIDTH_WORDS-1:0] addr,
    output logic [DATA_WIDTH-1:0] dread
);

    timeunit 1ns; timeprecision 1ns;

    localparam int RomSize = 2 ** ADDR_WIDTH_WORDS;

    logic [DATA_WIDTH-1:0] rom_mem[RomSize];

    initial begin
        $readmemh(ROM_FILE, rom_mem);
    end

    assign dread = rom_mem[addr];

endmodule : rom_async
