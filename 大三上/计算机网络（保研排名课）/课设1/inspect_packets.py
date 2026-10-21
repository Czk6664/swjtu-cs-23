#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 pcapng 文件中的数据包结构
"""

from scapy.all import rdpcap

def inspect_packets(filename):
    """检查数据包的详细结构"""
    print(f"正在读取文件: {filename}\n")
    
    packets = rdpcap(filename)
    print(f"总数据包数量: {len(packets)}\n")
    
    # 检查前10个包的详细信息
    print("=" * 80)
    print("前 10 个数据包的详细信息:")
    print("=" * 80)
    
    for i in range(min(10, len(packets))):
        pkt = packets[i]
        print(f"\n包 #{i + 1}:")
        print("-" * 80)
        print(pkt.show(dump=True))
        print("-" * 80)
        
        # 显示层次结构
        print(f"层次: {pkt.layers()}")
        
        # 显示以太网类型
        if hasattr(pkt, 'type'):
            print(f"EtherType: 0x{pkt.type:04x}")
        
        print()

if __name__ == "__main__":
    inspect_packets("ppoe.pcapng")
