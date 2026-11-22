// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026  Nicolas Gabriel Cotti

`include "uart_h.svh"

/// @brief Based on PrimeCell UART
///
/// The UART has the following features:
/// * Oversampling by 16
/// * Full-duplex asynchronous communication.
/// * Only standard baud rates supported:
///     {9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600}
/// * 1 or 2 stop bits.
/// * Parity control.
module uart #(
    parameter int FIFO_SIZE=32
)
(
    input logic clk,
    input logic rstN,
    input logic [1:0] reg_addr,
    input logic [31:0] reg_in,
    input logic we,
    output logic [31:0] reg_out
);

    timeunit 1ns; timeprecision 1ns;

    import uart_h::*;

    fifo #(
        .DATA_WIDTH(8),
        .SIZE_WORDS(FIFO_SIZE)
    ) fifo_i (
        .clk(clk),
        .rstN(rstN),
        .din(),
        .push(),
        .pop(),
        .dout(),
        .empty(),
        .full(),
        .num()
    );

    uart_regs_t default_uart_regs = '{
        f: '{
            REG0: '0,
            REG1: '0,
            REG2: '0,
            REG3: '0
        }
    };

    uart_regs_t uart_regs;

    always_ff @(posedge clk) begin
        if (!rstN) begin
            uart_regs <= default_uart_regs;
            reg_out <= '0;
        end else begin
            uart_regs <= uart_regs;
            reg_out <= uart_regs.r[reg_addr];

            if (we) begin
                uart_regs.r[reg_addr] <= reg_in;
            end
        end
    end

endmodule: uart
