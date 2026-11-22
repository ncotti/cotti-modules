// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026  Nicolas Gabriel Cotti

`ifndef UART_REGS_H_
`define UART_REGS_H_

package uart_h;

timeunit 1ns; timeprecision 1ns;

typedef union packed {
    struct packed {
        logic [31:0] REG0;
        logic [31:0] REG1;
        logic [31:0] REG2;
        logic [31:0] REG3;
    } f;
    logic [3:0][31:0] r;
} uart_regs_t;

endpackage: uart_h

`endif // UART_REGS_H_
