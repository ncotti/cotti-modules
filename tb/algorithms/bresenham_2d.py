# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti

import math
import random
from enum import Enum

import pyuvm
from bresenham import bresenham
from cocotb.clock import Clock
from cocotb.queue import QueueEmpty
from cocotb.triggers import FallingEdge
from cotti_uvm import (
    Bfm,
    Coverage,
    Item,
    Sequence,
    Tester,
    config_db_get,
    config_db_set,
)


# TODO, add to cotti-uvm as helper
def to_signed(a:int, width:int) -> int:
    """Converts an integer from the range [0;255] to [-128:127]"""
    max_unsigned_value = (2** width) - 1
    max_signed_value = (2 ** (width-1)) - 1
    if (a >= 0 and a <= max_signed_value):
        return a
    elif (a > max_signed_value and a <= max_unsigned_value):
        return a - (max_unsigned_value + 1)
    else:
        return max_unsigned_value


class LineItem(Item):
    def __init__(self, x0: int = 0, x1: int = 0,
        y0: int = 0, y1: int = 0, start: bool = False):
        super().__init__("line_item")
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.start = start

    async def delay(self, item) -> None:
        dx = abs(item.x1 - item.x0)
        dy = abs(item.y1 - item.y0)

        line_length = max(dx, dy) + 1

        for i in range(line_length):
            await FallingEdge(self.dut.clk)

        await FallingEdge(self.dut.clk)


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
                x0 = to_signed(int(self.dut.x0.value), self.width)
                x1 = to_signed(int(self.dut.x1.value), self.width)
                y0 = to_signed(int(self.dut.y0.value), self.width)
                y1 = to_signed(int(self.dut.y1.value), self.width)

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
            x = to_signed(int(self.dut.x.value), self.width)
            y = to_signed(int(self.dut.y.value), self.width)

            if start and not prev_start:
                line = []
                is_drawing = True

            if is_drawing:
                line.append((x, y))

            if last:
                self.output_monitor_queue.put_nowait(line)
                is_drawing = False

            prev_start = start


class LineEnum(Enum):
    """Coverage cases for the Bresenham's line algorithm.

    R0-R7 represent the regions of the plane, where R0 is the region from 0° to 45° degress.
    """
    R0 = 0,
    R1 = 1,
    R2 = 2,
    R3 = 3,
    R4 = 4,
    R5 = 5,
    R6 = 6,
    R7 = 7,
    DX_0 = 8,
    DY_0 = 9,
    SAME_START_END = 10,

class BresenhamCoverage(Coverage):
    coverage_enum = LineEnum

    def item_to_coverage(self, item: LineItem, output: list[(int, int)]) -> list[LineEnum]:
        out = []

        dx = item.x1 - item.x0
        dy = item.y1 - item.y0

        if dx > 0 and dy > 0 and abs(dy) <= abs(dx):
            out.append(LineEnum.R0)

        elif dx > 0 and dy > 0 and abs(dy) > abs(dx):
            out.append(LineEnum.R1)

        elif dx <= 0 and dy > 0 and abs(dy) > abs(dx):
            out.append(LineEnum.R2)

        elif dx <= 0 and dy > 0 and abs(dy) <= abs(dx):
            out.append(LineEnum.R3)

        elif dx <= 0 and dy <= 0 and abs(dy) <= abs(dx):
            out.append(LineEnum.R4)

        elif dx <= 0 and dy <= 0 and abs(dy) > abs(dx):
            out.append(LineEnum.R5)

        elif dx > 0 and dy <= 0 and abs(dy) > abs(dx):
            out.append(LineEnum.R6)

        else:
            out.append(LineEnum.R7)

        if (dx == 0):
            out.append(LineEnum.DX_0)

        if (dy == 0):
            out.append(LineEnum.DY_0)

        if (dx == 0 and dy == 0):
            out.append(LineEnum.SAME_START_END)
        return out


class CircularSeq(Sequence):
    """Lines every 30° (aprox), from 0° to 330°"""
    def items(self) -> list[LineItem]:
        out = []
        width = config_db_get("WIDTH")

        assert width > 5

        h = 12

        for angle in range(0, 360, 30):
            line = LineItem(
                x0=0,
                y0=0,
                x1=math.floor(h * math.cos(float(angle) / 180 * math.pi)),
                y1=math.floor(h * math.sin(float(angle) / 180 * math.pi)),
                start=True,
            )
            out.append(line)

        return out

class DiagonalSeq(Sequence):
    """Lines at exactly 45, 135°, 235° and 315° degree."""
    def items(self) -> list[LineItem]:
        out = []
        width = config_db_get("WIDTH")
        assert width > 5

        h = 8
        for angle in range(45, 360, 90):
            line = LineItem(
                x0=0,
                y0=0,
                x1=h if math.cos(float(angle) / 180 * math.pi) > 0 else -h,
                y1=h if math.sin(float(angle) / 180 * math.pi) > 0 else -h,
                start=True,
            )
            out.append(line)

        return out


class SamePointSeq(Sequence):
    def items(self) -> list[LineItem]:
        width = config_db_get("WIDTH")
        min_point = - 2 ** (width-1)
        max_point = (2 ** (width-1)) - 1

        rand_value = random.randint(min_point, max_point)
        return [
            LineItem(
                x0=rand_value,
                y0=rand_value,
                x1=rand_value,
                y1=rand_value,
                start=True
            )
        ]


class RandomSeq(Sequence):
    def items(self) -> list[LineItem]:
        out = []
        width = config_db_get("WIDTH")

        min_point = - 2 ** (width-6)
        max_point = (2 ** (width-6)) - 1

        for i in range(1):
            x0 = random.randint(min_point, max_point)
            x1 = random.randint(min_point, max_point)
            y0 = random.randint(min_point, max_point)
            y1 = random.randint(min_point, max_point)
            item = LineItem(x0=x0, x1=x1, y0=y0, y1=y1, start=True)
            out.append(item)

        return out


@pyuvm.test()
class RandomTest(Tester):
    bfm = BresenhamBfm
    golden_ref = golden_ref
    sequence = [CircularSeq, DiagonalSeq, SamePointSeq]
    coverage = BresenhamCoverage
    end_delay_ns = 2000
