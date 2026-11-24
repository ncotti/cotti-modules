
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
    output logic [WIDTH-1:0] num,
    output logic last
);

timeunit 1ns; timeprecision 1ns;

logic signed [WIDTH-1:0] x1_reg;
logic signed [WIDTH-1:0] y1_reg;

logic signed [WIDTH-1:0] dx, dx_input, dx_mod;
logic signed [WIDTH-1:0] dy, dy_input, dy_mod;

logic signed [WIDTH-1:0] x_add;
logic signed [WIDTH-1:0] y_add;

logic signed [WIDTH-1:0] error_x;
logic signed [WIDTH-1:0] error_y;

// This is equivalent to the "2D" variable in the docs.
logic signed [WIDTH-1:0] error;

logic x_move, y_move;
logic last_comb;
logic drawing;

assign dx_input = x1 - x0;
assign dy_input = y1 - y0;

assign dx_mod = (dx[WIDTH-1]) ? -dx : dx;
assign dy_mod = (dy[WIDTH-1]) ? -dy : dy;

assign x_add = (dx > 0) ? WIDTH'(1) : WIDTH'(0);
assign y_add = (dy > 0) ? WIDTH'(1) : WIDTH'(0);

assign error_x = (dx > 0) ? (dy << 1) : (-dy << 1);
assign error_y = (dy > 0) ? (-dx << 1) : (dx << 1);

assign x_move = (dx_mod > dy_mod) || error < 0;
assign y_move = (dy_mod > dx_mod) || error >= 0;

assign last_comb = (x == x1_reg) && (y == y1_reg);

assign last = (drawing) ? last_comb : 1'b0;

always_ff @(posedge clk) begin
    if (start) begin
        dx <= dx_input;
        dy <= dy_input;
        x1_reg <= x1;
        y1_reg <= y1;
        num <= '0;
        drawing <= 1'b1;

        x <= x0;
        y <= y0;
        error <= (dy_input << 1) - dx_input;
    end else begin
        dx <= dx;
        dy <= dy;
        x1_reg <= x1_reg;
        y1_reg <= y1_reg;
        if (!last_comb) begin
            x <= (x_move) ? x + x_add : x;
            y <= (y_move) ? y + y_add : y;
            num <= num + 1;
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
            num <= num;
            error <= error;
            drawing <= 1'b0;
        end
    end
end

endmodule: bresenham_2d
