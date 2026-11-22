
V_TB_TOP ?= clock_divider

V_SRC_DIRS += rtl/memories
V_TEST_DIRS += tb/memories

V_SRC_DIRS += rtl/fifos
V_TEST_DIRS += tb/fifos

# V_SRC_DIRS += rtl/uart
# V_INC_DIRS += rtl/uart

V_SRC_DIRS += rtl/clock
V_TEST_DIRS += tb/clock

include cotti-make/cottimake.mk