# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti

import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
from cocotb.queue import QueueEmpty

from cotti_uvm.bfm import Bfm
from pyuvm import uvm_sequence_item
from cotti_uvm.coverage import Coverage

import pyuvm

from cotti_uvm.common.help import config_db_set, config_db_get
from cotti_uvm.tester import Tester
from cotti_uvm.sequencer import Sequence

from enum import Enum

## DATA_WIDTH=32 ADDR_WIDTH_WORDS=4 ROM_FILE="tb/memories/hex/rom_sync.hex"

def read_hex_file(filename) -> list:
    with open(filename, "r") as file:
        return [int(line.strip(), 16) for line in file if line.strip()]

class Item(uvm_sequence_item):
    def __init__(self, raddr:int=0):
        super().__init__("rom_item")
        self.raddr = raddr

    def __eq__(self, other):
        return (self.raddr == other.raddr)

    def __str__(self):
        return f"raddr: {self.raddr}"


ROM = []

def golden_ref(item: Item):
    """ROM's golden reference function"""
    return ROM[item.raddr]

class RomBfm(Bfm):
    async def input_driver(self):
        self.dut.raddr.value = 0

        while True:
            await FallingEdge(self.dut.clk)
            try:
                item = self.input_driver_queue.get_nowait()
            except QueueEmpty:
                continue

            self.dut.raddr.value = item.raddr

    async def input_monitor(self):
        last_raddr = None
        while True:
            await FallingEdge(self.dut.clk)
            raddr = int(self.dut.raddr.value)
            if (last_raddr != raddr):
                self.input_monitor_queue.put_nowait(Item(raddr))

            last_raddr = raddr

    async def output_monitor(self):
        last_rdata = None
        while True:
            await FallingEdge(self.dut.clk)
            rdata = int(self.dut.rdata.value)
            if (last_rdata != rdata):
                self.output_monitor_queue.put_nowait(rdata)

            last_rdata = rdata

    def on_start(self):
        c = Clock(self.dut.clk, 2, "ns")
        c.start()

        self.data_width = int(self.dut.DATA_WIDTH.value)
        self.rom_size = 2 ** int(self.dut.ADDR_WIDTH_WORDS.value)

        config_db_set("DATA_WIDTH", self.data_width)
        config_db_set("ROM_SIZE", self.rom_size)

        global ROM
        ROM = read_hex_file(self.dut.ROM_FILE.value.decode("utf-8"))

class CoverageSet(Enum):
    FIRST_ADDR = 0,
    LAST_ADDR = 1,
    MIDDLE_ADDR = 2,

class RomCoverage(Coverage):
    coverage_set = set(CoverageSet)

    def write(self, item):
        result = None
        rom_size = config_db_get("ROM_SIZE")
        if (item.raddr == 0):
            result = CoverageSet.FIRST_ADDR
        elif (item.raddr == rom_size - 1):
            result = CoverageSet.LAST_ADDR
        else:
            result = CoverageSet.MIDDLE_ADDR
        self.coverage_checklist.add(result)

class RandomSeq(Sequence):
    def items(self) -> list[Item]:
        out = []
        rom_size = config_db_get("ROM_SIZE")
        for i in range(rom_size):
            item = Item(i)
            out.append(item)
        return out

@pyuvm.test()
class RandomTest(Tester):
    bfm = RomBfm
    golden_ref = golden_ref
    sequence = RandomSeq
    coverage = RomCoverage
    end_delay_ns=10