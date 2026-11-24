# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti

from enum import Enum

import pyuvm
from cotti_uvm import Item, config_db_get, config_db_set, Bfm, Coverage, Sequence, Tester
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb.queue import QueueEmpty
import random

from bresenham import bresenham

class LineItem(Item):
    def __init__(self, x0: int = 0, x1: int = 0,
        y0: int = 0, y1: int = 0, start: bool = False):
        super().__init__("fifo_item")
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.start = start

    def __eq__(self, other):
        return (self.x0 == other.x0) and \
            (self.x1 == other.x1) and \
            (self.y0 == other.y0) \
            (self.y1 == other.y1) \
            (self.start == other.start)

    def __str__(self):
        return (f"(x0,y0): ({self.x0},{self.y0}), "
            f"(x1,y1): ({self.x1},{self.y1}), "
            f"start: {self.start})")

def golden_ref(item: LineItem) -> list[(int,int)]:
    if (item.start):
        return list(bresenham(x0=item.x0, x1=item.x1, y0=item.y0, y1=item.y1))
    else:
        return []

class BresenhamBfm(Bfm):
    def on_start(self):
        Clock(self.dut.clk, 2, "ns").start()

        self.width = int(self.dut.WIDTH.value)
        config_db_set("WIDTH", self.width)

    async def input_driver(self):
        self.dut.start.value = 0
        while True:
            await FallingEdge(self.dut.clk)
            try:
                item = self.input_driver_queue.get_nowait()
                self.dut.start.value = item.start
                self.dut.x0.value = item.x0
                self.dut.x1.value = item.x1
                self.dut.y0.value = item.y0
                self.dut.y1.value = item.y1
            except QueueEmpty:
                self.dut.start.value = 0

    async def input_monitor(self):
        prev_start = False
        while True:
            await FallingEdge(self.dut.clk)
            start = bool(self.dut.start.value)

            if start and not prev_start:
                x0 = int(self.dut.x0.value)
                x1 = int(self.dut.x1.value)
                y0 = int(self.dut.y0.value)
                y1 = int(self.dut.y1.value)
                item = LineItem(
                    x0=x0,
                    x1=x1,
                    y0=y0,
                    y1=y1,
                    start=start,
                )
                self.input_monitor_queue.put_nowait(item)

            prev_start = start

    async def output_monitor(self):
        line = []
        prev_start = False
        is_drawing = False
        while True:
            await FallingEdge(self.dut.clk)
            start = bool(self.dut.start.value)
            last = bool(self.dut.last.value)
            num = int(self.dut.num.value)
            x = int(self.dut.x.value)
            y = int(self.dut.y.value)

            if start and not prev_start:
                line = []
                is_drawing = True

            if is_drawing:
                line.append((x, y))

            if last:
                self.output_monitor_queue.put_nowait(line)
                is_drawing = False

            prev_start = start


# class LineEnum(Enum):
#     FULL = 0

# class FifoCoverage(Coverage):
#     coverage_enum = FifoEnum

#     def item_to_coverage(self, item: FifoItem, output: FifoOut) -> list[FifoEnum]:
#         out = []
#         if output.empty:
#             out.append(FifoEnum.EMPTY)

#         if output.full:
#             out.append(FifoEnum.FULL)

#         if not item.pop and not item.push:
#             out.append(FifoEnum.NO_POP_NO_PUSH)
#         elif not item.pop and item.push:
#             out.append(FifoEnum.NO_POP_PUSH)
#         elif item.pop and not item.push:
#             out.append(FifoEnum.POP_NO_PUSH)
#         else:
#             out.append(FifoEnum.POP_PUSH)

#         if item.push and output.prev_full:
#             out.append(FifoEnum.PUSH_ON_FULL)

#         if item.pop and output.prev_empty:
#             out.append(FifoEnum.POP_ON_EMPTY)

#         if item.pop and item.push and output.prev_empty:
#             out.append(FifoEnum.PUSH_POP_ON_EMPTY)

#         if item.pop and item.push and output.prev_full:
#             out.append(FifoEnum.PUSH_POP_ON_FULL)

#         if not item.rstN and not output.prev_empty:
#             out.append(FifoEnum.RESET_AND_NOT_EMPTY)

#         return out


class RandomSeq(Sequence):
    def items(self) -> list[LineItem]:
        out = []
        width = config_db_get("WIDTH")

        min_point = - 2 ** (width-1)
        max_point = (2 ** (width-1)) - 1

        item = LineItem(x0=0, x1=6, y0=1, y1=4, start=True)

        out.append(item)

        return out


@pyuvm.test()
class RandomTest(Tester):
    bfm = BresenhamBfm
    golden_ref = golden_ref
    sequence = RandomSeq
    #coverage = FifoCoverage
    end_delay_ns = 50
