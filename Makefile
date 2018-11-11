PACKAGE_NAME := template_specialize

PYTHON_VERSIONS := \
    3.7.1 \
    3.6.7 \
    3.5.6 \
    3.4.9

ifeq '$(wildcard .makefile)' ''
    $(info Downloading base makefile...)
    $(shell curl -s -o .makefile 'https://raw.githubusercontent.com/craigahobbs/chisel/master/Makefile.base')
endif
include .makefile
