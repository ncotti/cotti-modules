// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026  Nicolas Gabriel Cotti
`include "bresenham_h.svh"

/// @brief Bresenham's algorithm implementation.
///
/// Given the (x,y) start and end coordinates of a line, this module
/// returns all the points that form that line, one per clock cycle.
/// E.g:
/// (-1, -4) -> (3,2)
/// (-1, -4), (0, -3), (0, -2), (1, -1), (2, 0), (2, 1), (3, 2)
///
/// Explanation:
/// First, you need to define in which of the eight directions the line is going,
/// by dividing the 360° angle space in 45° degrees each.
///
/// Let's say that the lines goes between 0°-45°, i.e., right and up. In that case,
/// every new point of the line is formed by two possible options:
/// (x+1, y), (x+1, y+1)
/// How the line is drawn will depend of its slope. E.g., a 0° degree line
/// will only be incremented in the x-axis, a 45° degree line will be
/// incremented in both the x-axis and y-axis, and a 30° line will be incremented
/// sometimes in both axis, and sometimes solely on the x-axis.
///
/// Ref: https://en.wikipedia.org/wiki/Bresenham's_line_algorithm
///
/// @param WIDTH Bit width of the X and Y axis values.
/// @param x0 Line's start x-coordinate.
/// Value is allowed to change between operations.
/// @param y0 Line's start y-coordinate.
/// Value is allowed to change between operations.
/// @param x1 Line's end x-coordinate.
/// Value is allowed to change between operations.
/// @param y1 Line's end y-coordinate.
/// Value is allowed to change between operations.
/// @param start Start drawing the line. When a rising edge is detected,
/// on the next clock cycle, the `x0` and `y0` will be outputted,
/// and each new point after that.
/// @param x Current line's point x-coordinate.
/// @param y Current line's point y-coordinate.
/// @param Point number, being "0" the first point.
/// @param last When `x == x1` and `y == y1`, a pulse is sent indicating
/// that this is the last point of the line.
module bresenham_2d #(
    parameter int WIDTH=8
)(
    input logic clk,
    input logic signed [WIDTH-1:0] x0,
    input logic signed [WIDTH-1:0] y0,
    input logic signed [WIDTH-1:0] x1,
    input logic signed [WIDTH-1:0] y1,
    input logic start,
    output logic [WIDTH-1:0] x,
    output logic [WIDTH-1:0] y,
    output logic last
);

import bresenham_h::*;

timeunit 1ns; timeprecision 1ns;

logic signed [WIDTH-1:0] x1_reg;
logic signed [WIDTH-1:0] y1_reg;

logic signed [WIDTH-1:0] x_add;
logic signed [WIDTH-1:0] y_add;

// Note that the width is "WIDTH", and not "WIDTH-1".
// E.g., for an 8-bit WIDTH, `dx` maximum and minimum values would be:
// dx_max = 127 -(-128) = 255
// dx_min = -128 -127 = -255
// Therefore, we require an extra bit.
logic signed [WIDTH:0] dx, dx_input, dx_abs;
logic signed [WIDTH:0] dy, dy_input, dy_abs;

// Note that the width is "WIDTH+1".
// E.g., for an 8-bit WIDTH, maximum and minimum values for the errors are:
// error_max = 2 * dy = 510
// error_min = - 2 * dy = -510
// Therefore, we require two extra bits.
logic signed [WIDTH+1:0] error_x;
logic signed [WIDTH+1:0] error_y;
logic signed [WIDTH+1:0] error_initial;
logic signed [WIDTH+1:0] error;

logic x_move, y_move;
logic last_comb;
logic drawing;
logic prev_start;

region_t region, region_initial;

assign dx_input = x1 - x0;
assign dy_input = y1 - y0;

assign dx_abs = (dx_input[WIDTH]) ? -dx_input : dx_input;
assign dy_abs = (dy_input[WIDTH]) ? -dy_input : dy_input;

assign last_comb = (x == x1_reg) && (y == y1_reg);

assign last = (drawing) ? last_comb : 1'b0;

assign region_initial = region_t'({dx_input > 0, dy_input > 0, dy_abs > dx_abs});

always_comb begin
    unique case (region)
    R0: begin
        x_add = 1;
        y_add = 1;
        error_x = (dy << 1);
        error_y = -(dx << 1);
        x_move = 1'b1;
        y_move = error >= 0;
    end
    R1: begin
        x_add = 1;
        y_add = 1;
        error_x = (dy << 1);
        error_y = -(dx << 1);
        x_move = error <= 0;
        y_move = 1'b1;
    end
    R2: begin
        x_add = -1;
        y_add = 1;
        error_x = -(dy << 1);
        error_y = -(dx << 1);
        x_move = error >= 0;
        y_move = 1'b1;
    end
    R3: begin
        x_add = -1;
        y_add = 1;
        error_x = -(dy << 1);
        error_y = -(dx << 1);
        x_move = 1'b1;
        y_move = error <= 0;
    end
    R4: begin
        x_add = -1;
        y_add = -1;
        error_x = -(dy << 1);
        error_y = (dx << 1);
        x_move = 1'b1;
        y_move = error >= 0;
    end
    R5: begin
        x_add = -1;
        y_add = -1;
        error_x = -(dy << 1);
        error_y = (dx << 1);
        x_move = error <= 0;
        y_move = 1'b1;
    end
    R6: begin
        x_add = 1;
        y_add = -1;
        error_x = (dy << 1);
        error_y = (dx << 1);
        x_move = error >= 0;
        y_move = 1'b1;
    end
    R7: begin
        x_add = 1;
        y_add = -1;
        error_x = (dy << 1);
        error_y = (dx << 1);
        x_move = 1'b1;
        y_move = error <= 0;
    end
    endcase

    unique case (region_initial)
        R0: error_initial = (dy_input << 1) - dx_input;
        R1: error_initial = dy_input - (dx_input << 1);
        R2: error_initial = -dy_input - (dx_input << 1);
        R3: error_initial = -(dy_input << 1) - dx_input;
        R4: error_initial = -(dy_input << 1) + dx_input;
        R5: error_initial = -dy_input + (dx_input << 1);
        R6: error_initial = dy_input + (dx_input << 1);
        R7: error_initial = (dy_input << 1) + dx_input;
    endcase
end

// Rising edge of start
always_ff @(posedge clk) begin
    prev_start <= start;
end

always_ff @(posedge clk) begin
    if (start & ~prev_start) begin
        dx <= dx_input;
        dy <= dy_input;
        x1_reg <= x1;
        y1_reg <= y1;
        drawing <= 1'b1;

        x <= x0;
        y <= y0;

        region <= region_initial;
        error <= error_initial;
    end else begin
        dx <= dx;
        dy <= dy;
        x1_reg <= x1_reg;
        y1_reg <= y1_reg;
        if (!last_comb) begin
            x <= (x_move) ? x + x_add : x;
            y <= (y_move) ? y + y_add : y;
            drawing <= 1'b1;
            unique case ({x_move, y_move})
                2'b00: error <= error;
                2'b01: error <= error + error_y;
                2'b10: error <= error + error_x;
                2'b11: error <= error + error_x + error_y;
            endcase
        end
        else begin
            x <= x;
            y <= y;
            error <= error;
            drawing <= 1'b0;
        end
    end
end

endmodule: bresenham_2d
