PACKAGE_NAME := template_specialize

PYTHON_VERSIONS := \
    3.7.0 \
    3.6.6 \
    3.5.5 \
    3.4.8

COVERAGE_REPORT_ARGS := --fail-under 91

$(shell if [ ! -f .makefile ]; then curl -s -o .makefile 'https://raw.githubusercontent.com/craigahobbs/chisel/master/Makefile.base'; fi)
include .makefile
