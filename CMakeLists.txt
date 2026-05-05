# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.2.0)
set(toolchainVersion 14_2_Rel1)
set(picotoolVersion 2.2.0-a4)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()
# ====================================================================================
set(PICO_BOARD pico2 CACHE STRING "Board type")

cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(HW10_serial_pgz_demo C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(HW10_serial_pgz_demo
    HW10_pico_main.c
    mpu6050.c
)

target_link_libraries(HW10_serial_pgz_demo
    pico_stdlib
    hardware_i2c
    hardware_gpio
)

pico_enable_stdio_usb(HW10_serial_pgz_demo 1)
pico_enable_stdio_uart(HW10_serial_pgz_demo 0)

pico_add_extra_outputs(HW10_serial_pgz_demo)
