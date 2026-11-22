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
logic [DIV_WIDTH-1:0] real_div_reg;
logic change_clock;

assign real_div = div - 1;
assign change_clock = (real_div != real_div_reg || div == '0);

always_ff @(posedge clk_f, negedge clk_f) begin
    if (div == '0) begin
        counter <= '1;
        clk_s <= 1'b0;
        real_div_reg <= '1;
    end
    else begin
        if (counter == real_div_reg) begin
            if (change_clock & ~clk_s) begin
                if (clk_f) begin
                    // Both clocks are on rising edge, can change safely
                    counter <= '0;
                    clk_s <= ~clk_s;
                    real_div_reg <= real_div;
                end else begin
                    // Wait until rising edge of clk_f
                    counter <= counter;
                    clk_s <= clk_s;
                    real_div_reg <= real_div_reg;
                end
            end else begin
                counter <= '0;
                clk_s <= ~clk_s;
                real_div_reg <= real_div_reg;
            end
        end else begin
            counter <= counter + 1;
            clk_s <= clk_s;
            real_div_reg <= real_div_reg;
        end
    end
end


endmodule: clock_divider
