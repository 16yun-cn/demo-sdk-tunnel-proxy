CXX = g++
CXXFLAGS = -O2 -std=c++17
PKG_CONFIG ?= pkg-config

CPR_CFLAGS := $(shell $(PKG_CONFIG) --cflags libcpr 2>/dev/null || echo "")
CPR_LIBS := $(shell $(PKG_CONFIG) --libs libcpr 2>/dev/null || echo "-lcpr -lcurl")

TARGET = main
SRC = main.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) $(CPR_CFLAGS) -o $@ $< $(CPR_LIBS)

clean:
	rm -f $(TARGET)

.PHONY: all clean
