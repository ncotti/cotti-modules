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

    timeunit 1ns;
    timeprecision 1ns;

    localparam int PtrWidth = (SIZE_WORDS > 1) ? $clog2(SIZE_WORDS) : 1;

    logic [PtrWidth-1:0] read_pointer, write_pointer;

    logic [DATA_WIDTH-1:0] ram_dout;
    logic [DATA_WIDTH-1:0] head_reg;

    logic do_push, do_pop;
    logic replace_head;
    logic we;
    logic ram_read_valid;

    assign empty = (num == '0);
    assign full  = (num == ($clog2(SIZE_WORDS+1))'(SIZE_WORDS));

    // Accepted FIFO operations.
    assign do_pop  = pop & ~empty;
    assign do_push = push & (~full | do_pop);

    // Replacing the only element in the FIFO.
    assign replace_head = do_push & do_pop & (num == 1);

    // The head is stored in head_reg.
    // Only subsequent elements are stored in RAM.
    assign we = do_push & ~empty & ~replace_head;

    // Select the RAM output after a successful pop when
    // there was another element waiting in the FIFO.
    assign dout = ram_read_valid ? ram_dout : head_reg;

    ram_simple_dual_port #(
        .DATA_WIDTH(DATA_WIDTH),
        .DATA_LANE_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH_WORDS(PtrWidth)
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

            head_reg <= '0;
            ram_read_valid <= 1'b0;
        end else begin

            // Keep the current output value.
            // When a RAM read becomes valid, this captures
            // its result on the following clock edge.
            if (do_push && empty)
                head_reg <= din;
            else if (replace_head)
                head_reg <= din;
            else
                head_reg <= dout;

            // The RAM output is selected immediately after
            // a pop if another element was available.
            ram_read_valid <= do_pop && (num > 1);

            // Update the number of stored elements.
            if (do_push && !do_pop)
                num <= num + 1'b1;
            else if (do_pop && !do_push)
                num <= num - 1'b1;

            // Advance the RAM read pointer when promoting
            // another element to the FIFO head.
            if (do_pop && (num > 1)) begin
                if (read_pointer == PtrWidth'(SIZE_WORDS - 1))
                    read_pointer <= '0;
                else
                    read_pointer <= read_pointer + 1'b1;
            end

            // Advance the RAM write pointer when appending
            // an element behind the current head.
            if (we) begin
                if (write_pointer == PtrWidth'(SIZE_WORDS - 1))
                    write_pointer <= '0;
                else
                    write_pointer <= write_pointer + 1'b1;
            end
        end
    end

endmodule: fifo_fwft
