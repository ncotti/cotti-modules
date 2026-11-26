
V_TB_TOP ?= bresenham_2d

V_SRC_DIRS += rtl/memories
V_TEST_DIRS += tb/memories

V_SRC_DIRS += rtl/fifos
V_TEST_DIRS += tb/fifos

# V_SRC_DIRS += rtl/uart
# V_INC_DIRS += rtl/uart

V_SRC_DIRS += rtl/clock
V_TEST_DIRS += tb/clock

V_SRC_DIRS += rtl/algorithms
V_INC_DIRS += rtl/algorithms/inc
V_TEST_DIRS += tb/algorithms

include cotti-make/cottimake.mk