module clock_divider #(
    parameter int DIV_WIDTH=16
)(
    input logic clk_f,
    input logic [DIV_WIDTH-1:0] div,
    output logic clk_s
);

timeunit 1ns; timeprecision 1ns;

logic [DIV_WIDTH-1:0] counter;
logic [DIV_WIDTH-1:0] real_div;

assign real_div = div -1;

always_ff @(posedge clk_f, negedge clk_f) begin
    if (div == '0) begin
        counter <= '0;
        clk_s <= 1'b0;
    end
    else begin
        if (counter == real_div) begin
            counter <= '0;
            clk_s <= ~clk_s;
        end else begin
            counter <= counter + 1;
            clk_s <= clk_s;
        end
    end
end


endmodule: clock_divider
