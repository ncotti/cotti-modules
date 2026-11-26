`ifndef BRESENHAM_H_
`define BRESENHAM_H_

package bresenham_h;

timeunit 1ns; timeprecision 1ns;

/// @brief The X-Y plane can be separated in 8 planes based on the properties
/// of dx and dy:
/// * [2] dx > 0
/// * [1] dy > 0
/// * [0] |dy| > |dx|
///
/// Here, "R0" corresponds to angles 0°-45°, and goes counter-clockwise until R7.
typedef enum logic [2:0] {
    R0 = 3'b110,
    R1 = 3'b111,
    R2 = 3'b011,
    R3 = 3'b010,
    R4 = 3'b000,
    R5 = 3'b001,
    R6 = 3'b101,
    R7 = 3'b100
} region_t;

endpackage: bresenham_h

`endif // BRESENHAM_H_
