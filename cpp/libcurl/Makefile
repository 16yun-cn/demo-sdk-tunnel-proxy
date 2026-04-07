CXX := g++
CXXFLAGS := -O2 -std=c++17
LDFLAGS := -lcurl

all: main

main: main.cpp
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f main

