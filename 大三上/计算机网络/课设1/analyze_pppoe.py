#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPPoE 数据包分析脚本
分析 ppoe.pcapng 文件中的 PPPoE 协议数据包
"""

import sys
from collections import Counter

try:
    from scapy.all import rdpcap, PPPoE, PPPoED
    from scapy.all import Ether, IP, TCP, UDP, ICMP
except ImportError:
    print("错误: 需要安装 scapy 库")
    print("请运行: pip install scapy")
    sys.exit(1)

def analyze_pppoe_pcap(filename):
    """分析 PPPoE pcap 文件"""
    print(f"正在分析文件: {filename}")
    print("=" * 80)
    
    try:
        packets = rdpcap(filename)
        print(f"\n总数据包数量: {len(packets)}\n")
    except Exception as e:
        print(f"读取文件失败: {e}")
        return
    
    # 统计信息
    pppoe_discovery_count = 0
    pppoe_session_count = 0
    pppoe_types = Counter()
    mac_addresses = set()
    session_ids = set()
    
    # PPPoE Discovery 阶段的包
    padi_packets = []
    pado_packets = []
    padr_packets = []
    pads_packets = []
    padt_packets = []
    
    # PPPoE Session 阶段的包
    session_packets = []
    
    print("开始分析数据包...\n")
    
    for i, pkt in enumerate(packets):
        # 检查以太网层
        if Ether in pkt:
            mac_addresses.add(pkt[Ether].src)
            mac_addresses.add(pkt[Ether].dst)
        
        # 检查 PPPoE Discovery 包
        if PPPoED in pkt:
            pppoe_discovery_count += 1
            code = pkt[PPPoED].code
            
            if code == 0x09:  # PADI
                pppoe_types['PADI'] += 1
                padi_packets.append((i, pkt))
            elif code == 0x07:  # PADO
                pppoe_types['PADO'] += 1
                pado_packets.append((i, pkt))
            elif code == 0x19:  # PADR
                pppoe_types['PADR'] += 1
                padr_packets.append((i, pkt))
            elif code == 0x65:  # PADS
                pppoe_types['PADS'] += 1
                pads_packets.append((i, pkt))
                if pkt[PPPoED].sessionid:
                    session_ids.add(pkt[PPPoED].sessionid)
            elif code == 0xa7:  # PADT
                pppoe_types['PADT'] += 1
                padt_packets.append((i, pkt))
        
        # 检查 PPPoE Session 包
        if PPPoE in pkt:
            pppoe_session_count += 1
            session_packets.append((i, pkt))
            if pkt[PPPoE].sessionid:
                session_ids.add(pkt[PPPoE].sessionid)
    
    # 打印统计结果
    print("=" * 80)
    print("PPPoE 数据包统计")
    print("=" * 80)
    print(f"PPPoE Discovery 包数量: {pppoe_discovery_count}")
    print(f"PPPoE Session 包数量: {pppoe_session_count}")
    print()
    
    print("PPPoE Discovery 阶段消息类型分布:")
    for msg_type, count in sorted(pppoe_types.items()):
        print(f"  {msg_type}: {count} 个")
    print()
    
    print(f"发现的 MAC 地址数量: {len(mac_addresses)}")
    for mac in sorted(mac_addresses):
        print(f"  {mac}")
    print()
    
    print(f"PPPoE Session ID 数量: {len(session_ids)}")
    for sid in sorted(session_ids):
        print(f"  Session ID: 0x{sid:04x} ({sid})")
    print()
    
    # 详细分析 PPPoE Discovery 阶段
    print("=" * 80)
    print("PPPoE Discovery 阶段详细分析")
    print("=" * 80)
    
    if padi_packets:
        print(f"\nPADI (PPPoE Active Discovery Initiation) - {len(padi_packets)} 个:")
        for idx, (pkt_num, pkt) in enumerate(padi_packets[:5]):  # 只显示前5个
            print(f"\n  包 #{pkt_num + 1}:")
            print(f"    源 MAC: {pkt[Ether].src}")
            print(f"    目标 MAC: {pkt[Ether].dst}")
            print(f"    Session ID: 0x{pkt[PPPoED].sessionid:04x}")
            if hasattr(pkt[PPPoED], 'tags'):
                print(f"    标签: {pkt[PPPoED].tags}")
    
    if pado_packets:
        print(f"\nPADO (PPPoE Active Discovery Offer) - {len(pado_packets)} 个:")
        for idx, (pkt_num, pkt) in enumerate(pado_packets[:5]):
            print(f"\n  包 #{pkt_num + 1}:")
            print(f"    源 MAC: {pkt[Ether].src}")
            print(f"    目标 MAC: {pkt[Ether].dst}")
            print(f"    Session ID: 0x{pkt[PPPoED].sessionid:04x}")
    
    if padr_packets:
        print(f"\nPADR (PPPoE Active Discovery Request) - {len(padr_packets)} 个:")
        for idx, (pkt_num, pkt) in enumerate(padr_packets[:5]):
            print(f"\n  包 #{pkt_num + 1}:")
            print(f"    源 MAC: {pkt[Ether].src}")
            print(f"    目标 MAC: {pkt[Ether].dst}")
            print(f"    Session ID: 0x{pkt[PPPoED].sessionid:04x}")
    
    if pads_packets:
        print(f"\nPADS (PPPoE Active Discovery Session-confirmation) - {len(pads_packets)} 个:")
        for idx, (pkt_num, pkt) in enumerate(pads_packets[:5]):
            print(f"\n  包 #{pkt_num + 1}:")
            print(f"    源 MAC: {pkt[Ether].src}")
            print(f"    目标 MAC: {pkt[Ether].dst}")
            print(f"    Session ID: 0x{pkt[PPPoED].sessionid:04x}")
    
    if padt_packets:
        print(f"\nPADT (PPPoE Active Discovery Terminate) - {len(padt_packets)} 个:")
        for idx, (pkt_num, pkt) in enumerate(padt_packets[:5]):
            print(f"\n  包 #{pkt_num + 1}:")
            print(f"    源 MAC: {pkt[Ether].src}")
            print(f"    目标 MAC: {pkt[Ether].dst}")
            print(f"    Session ID: 0x{pkt[PPPoED].sessionid:04x}")
    
    # 分析 PPPoE Session 阶段
    if session_packets:
        print("\n" + "=" * 80)
        print("PPPoE Session 阶段分析")
        print("=" * 80)
        print(f"\n总 Session 包数量: {len(session_packets)}")
        
        # 统计协议分布
        protocol_count = Counter()
        for _, pkt in session_packets:
            if IP in pkt:
                if TCP in pkt:
                    protocol_count['TCP'] += 1
                elif UDP in pkt:
                    protocol_count['UDP'] += 1
                elif ICMP in pkt:
                    protocol_count['ICMP'] += 1
                else:
                    protocol_count['其他IP'] += 1
            else:
                protocol_count['非IP'] += 1
        
        print("\nSession 包中的协议分布:")
        for proto, count in sorted(protocol_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  {proto}: {count} 个")
        
        # 显示前几个 session 包的详细信息
        print("\n前 5 个 PPPoE Session 包详情:")
        for idx, (pkt_num, pkt) in enumerate(session_packets[:5]):
            print(f"\n  包 #{pkt_num + 1}:")
            print(f"    Session ID: 0x{pkt[PPPoE].sessionid:04x}")
            if IP in pkt:
                print(f"    IP: {pkt[IP].src} -> {pkt[IP].dst}")
                if TCP in pkt:
                    print(f"    TCP: {pkt[TCP].sport} -> {pkt[TCP].dport}")
                elif UDP in pkt:
                    print(f"    UDP: {pkt[UDP].sport} -> {pkt[UDP].dport}")
    
    print("\n" + "=" * 80)
    print("分析完成!")
    print("=" * 80)

if __name__ == "__main__":
    analyze_pppoe_pcap("ppoe.pcapng")
