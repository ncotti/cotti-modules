/// @brief This is a synchronous ROM memory, whose values are preloaded with
/// the contents of the file `ROM_FILE`. It is synthesizable.
///
/// @param DATA_WIDTH Number of bits for each stored word.
/// @param ADDR_WIDTH_WORDS Number of bits addressing the data.
/// This parameter defines the size of the ROM, as `2^ADDR_WIDTH` **words**
/// will be stored.
/// @param clk Clock signal.
/// @param addr Address of the data to be retrieved in the next clock cycle.
/// @param dread Data read from prev `addr`.
module rom_sync #(
    int DATA_WIDTH = 32,
    int ADDR_WIDTH_WORDS = 4,
    string ROM_FILE = "tb/memories/rom_sync.hex"
) (
    input logic clk,
    input logic [ADDR_WIDTH_WORDS-1:0] addr,
    output logic [DATA_WIDTH-1:0] dread
);

    timeunit 1ns; timeprecision 1ns;

    localparam int RomSize = 2 ** ADDR_WIDTH_WORDS;

    logic [DATA_WIDTH-1:0] rom_mem[RomSize];

    initial begin
        $readmemh(ROM_FILE, rom_mem);
    end

    always_ff @(posedge clk) begin
        dread <= rom_mem[addr];
    end

endmodule : rom_sync
