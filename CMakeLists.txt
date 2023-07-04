cmake_minimum_required(VERSION 3.9)
project(vamos-spec LANGUAGES C CXX VERSION 0.1)

find_package(vamos-buffers REQUIRED)
get_filename_component(vamos-buffers_DIR ${vamos-buffers_DIR} ABSOLUTE)

if (NOT DEFINED ${vamos-hyper_DIR})
	message(STATUS "vamos-hyper_DIR not set, assuming vamos-hyper is in the same directory as vamos-buffers."
		       "If not true, set -Dvamos-hyper_DIR= ")
	string(REPLACE buffers hyper vamos-hyper_DIR ${vamos-buffers_DIR})
	message(STATUS "vamos-hyper_DIR=${vamos-hyper_DIR}")
endif()

if (NOT DEFINED ${vamos-sources_DIR})
	message(STATUS "vamos-sources_DIR not set, assuming vamos-sources is in the same directory as vamos-buffers."
		       "If not true, set -Dvamos-sources_DIR= ")
	string(REPLACE buffers sources vamos-sources_DIR ${vamos-buffers_DIR})
	message(STATUS "vamos-sources_DIR=${vamos-sources_DIR}")
endif()

if (NOT DEFINED ${vamos-common_DIR})
	message(STATUS "vamos-common_DIR not set, assuming vamos-common is in the same directory as vamos-buffers."
		       "If not true, set -Dvamos-common_DIR= ")
	string(REPLACE buffers common vamos-common_DIR ${vamos-buffers_DIR})
	message(STATUS "vamos-common_DIR=${vamos-common_DIR}")
endif()

find_package(vamos-hyper REQUIRED)
find_package(vamos-sources REQUIRED)
find_package(vamos-common REQUIRED)

if(NOT CMAKE_BUILD_TYPE)
	message(STATUS "Build type not set. Setting buffer's build type.")
	set(CMAKE_BUILD_TYPE ${vamos-buffers_BUILD_TYPE} CACHE STRING "" FORCE)
endif()

if (vamos-buffers_OPTION_ENABLE_IPO)
        set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
endif()

get_target_property(vamos-buffers_vamos-buffers-lib vamos-buffers-lib LOCATION)
get_target_property(vamos-buffers_vamos-buffers-ringbuf vamos-buffers-ringbuf LOCATION)
get_target_property(vamos-buffers_vamos-buffers-shmbuf vamos-buffers-shmbuf LOCATION)
get_target_property(vamos-buffers_vamos-buffers-streams vamos-buffers-streams LOCATION)
get_filename_component(vamos-buffers_LIBRARIES_DIRS_lib ${vamos-buffers_vamos-buffers-lib} DIRECTORY)
get_filename_component(vamos-buffers_LIBRARIES_DIRS_core ${vamos-buffers_vamos-buffers-ringbuf} DIRECTORY)
get_filename_component(vamos-buffers_LIBRARIES_DIRS_shmbuf ${vamos-buffers_vamos-buffers-shmbuf} DIRECTORY)
get_filename_component(vamos-buffers_LIBRARIES_DIRS_streams ${vamos-buffers_vamos-buffers-streams} DIRECTORY)

get_target_property(vamos-hyper_vamos-hyper-lib vamos-hyper-lib LOCATION)
get_filename_component(vamos-hyper_LIBRARIES_DIRS_lib ${vamos-hyper_vamos-hyper-lib} DIRECTORY)

message(STATUS "vamos-hyper CXX standard: ${vamos_hyper_CXX_STANDARD} (using it)")
set(CMAKE_VERBOSE_MAKEFILE 1)
set(CMAKE_CXX_STANDARD ${vamos_hyper_CXX_STANDARD})
set(CMAKE_CXX_STANDARD_REQUIRED ON)

get_filename_component(vamos-hyper_DIR ${vamos-hyper_DIR} ABSOLUTE)
get_filename_component(vamos-sources_DIR ${vamos-sources_DIR} ABSOLUTE)
get_filename_component(vamos-common_DIR ${vamos-common_DIR} ABSOLUTE)
set(vamos-hyper_INCLUDE_DIR "${vamos-hyper_DIR}/../../include")

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/config.py.in
	       ${CMAKE_CURRENT_SOURCE_DIR}/config.py)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/config.sh.in
	       ${CMAKE_CURRENT_SOURCE_DIR}/config.sh)

enable_testing()
add_subdirectory(tests)
