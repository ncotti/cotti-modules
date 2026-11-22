// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026  Nicolas Gabriel Cotti

/// @brief Clock divider.
///
/// Given a fast input clock `clk_f` with frequency "f", this module returns
/// an slower clock `clk_s` with frequency `f / div`.
/// @param DIV_WIDTH Number of bits used to for the divider.
/// Determines the maximum value of the divider as `2^DIV_WIDTH - 1`.
/// @param clk_f Fast clock input.
/// @param div Integer divisor.
/// A value of zero acts as a reset for the device, while keeping the output clock forcefully low.
/// A value of one outputs a clock with the same frequency as the one in the input.
/// A value greater than one divides the output frequency by `f / div`.
/// @param pol Polarity of the output clock.
/// * `pol = 0`: 0° phase. Both clocks change on the rising edge.
/// * `pol = 1`: 180° phase. The slow clock changes on the falling edge of the
/// fast clock.
/// @param clk_s Slow clock output.
module clock_divider #(
    parameter int DIV_WIDTH = 16
) (
    input logic clk_f,
    input logic [DIV_WIDTH-1:0] div,
    input logic pol,
    output logic clk_s
);

    timeunit 1ns; timeprecision 1ns;

    logic [DIV_WIDTH-1:0] counter;
    logic [DIV_WIDTH-1:0] real_div;
    logic [DIV_WIDTH-1:0] real_div_reg;
    logic pol_reg;
    logic change_clock;

    assign real_div = div - 1;
    assign change_clock = ((real_div != real_div_reg) || (pol_reg != pol) || (div == '0));

    always_ff @(posedge clk_f, negedge clk_f) begin
        if (div == '0) begin
            counter <= '1;
            clk_s <= 1'b0;
            real_div_reg <= real_div;
            pol_reg <= pol;
        end else begin
            if (counter == real_div_reg) begin
                if (change_clock && ~clk_s) begin
                    if (clk_f == pol) begin
                        // Both clocks are on rising edge, can change safely
                        counter <= '0;
                        clk_s <= ~clk_s;
                        real_div_reg <= real_div;
                        pol_reg <= pol;
                    end else begin
                        // Wait until rising edge of clk_f
                        counter <= counter;
                        clk_s <= clk_s;
                        real_div_reg <= real_div_reg;
                        pol_reg <= pol_reg;
                    end
                end else begin
                    counter <= '0;
                    clk_s <= ~clk_s;
                    real_div_reg <= real_div_reg;
                    pol_reg <= pol_reg;
                end
            end else begin
                counter <= counter + 1;
                clk_s <= clk_s;
                real_div_reg <= real_div_reg;
                pol_reg <= pol_reg;
            end
        end
    end


endmodule : clock_divider
