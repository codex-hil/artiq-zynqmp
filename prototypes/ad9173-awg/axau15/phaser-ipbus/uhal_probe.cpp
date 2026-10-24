#include <uhal/uhal.hpp>
#include <iostream>
#include <stdexcept>
int main(int argc,char**argv){
 if(argc!=3) return 2;
 uhal::setLogLevelTo(uhal::Error());
 auto hw=uhal::ConnectionManager::getDevice("alinx",argv[1],std::string("file://")+argv[2]);
 auto id=hw.getNode("identity").read();hw.dispatch();
 if(id.value()!=0x41585048) throw std::runtime_error("Wrong endpoint");
 auto before=hw.getNode("writes").read();hw.dispatch();
 for(unsigned i=0;i<256;i++)hw.getNode("scratch").write(0xa5000000|i);
 hw.dispatch();
 auto after=hw.getNode("writes").read();auto scratch=hw.getNode("scratch").read();hw.dispatch();
 if(after.value()-before.value()!=256 || scratch.value()!=0xa50000ff)throw std::runtime_error("Writes duplicated/lost");
 std::vector<uhal::ValVector<uint32_t>> blocks;
 for(unsigned i=0;i<256;i++)blocks.push_back(hw.getNode("held").readBlock(21));
 hw.dispatch();
 for(auto &b:blocks){if(b.size()!=21)throw std::runtime_error("Block length");for(unsigned i=0;i<21;i++)if(b[i]!=blocks[0][i])throw std::runtime_error("Block corruption");}
 std::cout<<"PASS official uHAL: identity,256 ordered scratch writes exactly once,256x21 pipelined read words\n";
}
