LDFLAGS=`pkg-config --libs gnash python2` -lgnashrender -Wl,-rpath,/usr/lib64/gnash
CXXFLAGS=-fPIC `pkg-config --cflags gnash python2` -I/mnt/downloadNT/TEMPF/mga/gnash/BUILD/gnash-0.8.10/lib{render,base,core}
oglgnash.so: oglgnash.o
	$(CXX) -o $@ $< $(LDFLAGS) -shared
