# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti

from enum import Enum

import pyuvm
from cotti_uvm import Item, config_db_get, config_db_set, Bfm, Coverage, Sequence, Tester
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb.queue import QueueEmpty
import random

##? DATA_WIDTH=32 SIZE_WORDS=8
###? DATA_WIDTH=16 SIZE_WORDS=5
###? DATA_WIDTH=25 SIZE_WORDS=3
###? DATA_WIDTH=7 SIZE_WORDS=2
###? DATA_WIDTH=7 SIZE_WORDS=1

class FifoItem(Item):
    def __init__(self, din:int=0, push:bool=False, pop:bool=False, rstN:bool = True):
        super().__init__("fifo_item")
        self.din = din
        self.push = push
        self.pop = pop
        self.rstN = rstN

    def __eq__(self, other):
        return ((self.din == other.din) and
                (self.push == other.push) and
                (self.pop == other.pop))

    def __str__(self):
        return f"din: {self.din:#X}; push: {self.push}; pop: {self.pop}"


class FifoOut:
    def __init__(self, dout:int, empty:bool, full:bool, num:int, prev_full:bool=False, prev_empty:bool=True):
        self.dout = dout
        self.empty = empty
        self.full = full
        self.num = num
        self.prev_full = prev_full
        self.prev_empty = prev_empty

    def __eq__(self, other):
        return (
            (self.dout == other.dout) and
            (self.empty == other.empty) and
            (self.full == other.full) and
            (self.num == other.num))

    def __str__(self):
        return f"Dout: {self.dout:#X}, num: {self.num}, empty: {self.empty}, full: {self.full}"

FIFO = []
LAST_FIFO_OUTPUT = 0

def golden_ref(item: FifoItem) -> FifoOut:
    global FIFO
    global LAST_FIFO_OUTPUT
    size_words = config_db_get("SIZE_WORDS")

    if (not item.rstN):
        dout = 0
        FIFO = []
    else:
        if (not item.pop and not item.push):
            dout = LAST_FIFO_OUTPUT
        elif (not item.pop and item.push):
            if (len(FIFO) == 0):
                dout = item.din
            else:
                dout = LAST_FIFO_OUTPUT

            if (len(FIFO) < size_words):
                FIFO.append(item.din)
        elif (item.pop and not item.push):
            if (len(FIFO) == 1):
                FIFO.pop(0)
                dout = LAST_FIFO_OUTPUT
            elif (len(FIFO) > 1):
                dout = FIFO.pop(1)
            else:
                dout = LAST_FIFO_OUTPUT
        else:
            if (len(FIFO) <= 1):
                dout = item.din
            else:
                FIFO.append(item.din)
                dout = FIFO.pop(1)

    empty = len(FIFO) == 0
    full = len(FIFO) == size_words
    num = len(FIFO)
    LAST_FIFO_OUTPUT = dout
    return FifoOut(
        dout=dout,
        empty=empty,
        full=full,
        num=num,
    )

class FifoBfm(Bfm):
    def on_start(self):
        Clock(self.dut.clk, 2, "ns").start()

        self.data_width = int(self.dut.DATA_WIDTH.value)
        self.size_words = int(self.dut.SIZE_WORDS.value)
        config_db_set("DATA_WIDTH", self.data_width)
        config_db_set("SIZE_WORDS", self.size_words)

    async def reset(self) -> None:
        await FallingEdge(self.dut.clk)
        self.dut.rstN.value = 0
        self.dut.pop.value = 0
        self.dut.push.value = 0
        await FallingEdge(self.dut.clk)
        self.dut.rstN.value = 1

    async def input_driver(self):
        self.dut.din.value = 0
        self.dut.pop.value = 0
        self.dut.push.value = 0
        self.dut.rstN.value = 1
        while True:
            await FallingEdge(self.dut.clk)
            try:
                item = self.input_driver_queue.get_nowait()
                self.dut.din.value = item.din
                self.dut.push.value = item.push
                self.dut.pop.value = item.pop
                self.dut.rstN.value = item.rstN
            except QueueEmpty:
                self.dut.pop.value = 0
                self.dut.push.value = 0

    async def input_monitor(self):
        while True:
            await FallingEdge(self.dut.clk)
            push = bool(self.dut.push.value)
            pop = bool(self.dut.pop.value)
            rstN = bool(self.dut.rstN.value)

            if (push or pop or not rstN):
                din = int(self.dut.din.value)
                item = FifoItem(
                    din=din,
                    push=push,
                    pop=pop,
                    rstN=rstN,
                )
                self.input_monitor_queue.put_nowait(item)

    async def output_monitor(self):
        prev_full = 0
        prev_empty = 1
        while True:
            await FallingEdge(self.dut.clk)
            push = bool(self.dut.push.value)
            pop = bool(self.dut.pop.value)
            rstN = bool(self.dut.rstN.value)

            num = int(self.dut.num.value)
            full = bool(self.dut.full.value)
            empty = bool(self.dut.empty.value)
            dout = int(self.dut.dout.value)

            if (push or pop or not rstN):
                out = FifoOut(dout = dout,
                    empty = empty,
                    full=full,
                    num=num,
                    prev_full=prev_full,
                    prev_empty=prev_empty,
                )
                self.output_monitor_queue.put_nowait(out)
            prev_empty = empty
            prev_full = full


class FifoEnum(Enum):
    FULL=0,
    EMPTY=1,
    NO_POP_NO_PUSH=2,
    NO_POP_PUSH=3,
    POP_NO_PUSH=4,
    POP_PUSH=5,
    PUSH_ON_FULL=6,
    POP_ON_EMPTY=7,
    PUSH_POP_ON_EMPTY=8,
    PUSH_POP_ON_FULL=9,
    RESET_AND_NOT_EMPTY=10

class FifoCoverage(Coverage):
    coverage_enum = FifoEnum

    def item_to_coverage(self, item:FifoItem, output:FifoOut) -> list[FifoEnum]:
        out = []
        if (output.empty):
            out.append(FifoEnum.EMPTY)

        if(output.full):
            out.append(FifoEnum.FULL)

        if(not item.pop and not item.push):
            out.append(FifoEnum.NO_POP_NO_PUSH)
        elif(not item.pop and item.push):
            out.append(FifoEnum.NO_POP_PUSH)
        elif(item.pop and not item.push):
            out.append(FifoEnum.POP_NO_PUSH)
        else:
            out.append(FifoEnum.POP_PUSH)

        if (item.push and output.prev_full):
            out.append(FifoEnum.PUSH_ON_FULL)

        if (item.pop and output.prev_empty):
            out.append(FifoEnum.POP_ON_EMPTY)

        if (item.pop and item.push and output.prev_empty):
            out.append(FifoEnum.PUSH_POP_ON_EMPTY)

        if (item.pop and item.push and output.prev_full):
            out.append(FifoEnum.PUSH_POP_ON_FULL)

        if (not item.rstN and not output.prev_empty):
            out.append(FifoEnum.RESET_AND_NOT_EMPTY)

        return out

class RandomSeq(Sequence):
    def items(self) -> list[FifoItem]:
        out = []
        size_words = config_db_get("SIZE_WORDS")
        data_width = config_db_get("DATA_WIDTH")

        # More likely push than pop, fill the FIFO
        pushed_words = 0
        while(pushed_words < size_words + 10):
            for i in range(size_words * 4):
                push = random.choices([0, 1], weights=[20, 80])[0]
                pop = random.choices([0, 1], weights=[80, 20])[0]
                item = FifoItem(
                    din = random.randint(0, (2**data_width) -1),
                    push= push,
                    pop= pop,
                )
                out.append(item)
                if (push and not pop):
                    pushed_words += 1

        # More likely pop than push, empty the fifo
        while (pushed_words > -10):
            push = random.choices([0, 1], weights=[80, 20])[0]
            pop = random.choices([0, 1], weights=[20, 80])[0]
            item = FifoItem(
                din = random.randint(0, (2**data_width) -1),
                push= push,
                pop= pop,
            )
            out.append(item)
            if (pop and not push):
                pushed_words -= 1

        # Sprinkle some reset behavior
        for i in range(size_words * 4 + 20):
            item = FifoItem(
                din = random.randint(0, (2**data_width) -1),
                push= 1,
                pop= 0,
                rstN= random.choices([0, 1], weights=[10, 90])[0],
            )
            out.append(item)

        return out

@pyuvm.test()
class RandomTest(Tester):
    bfm = FifoBfm
    golden_ref = golden_ref
    sequence = RandomSeq
    coverage = FifoCoverage