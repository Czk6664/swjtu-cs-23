#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析程泽凯.pcapng文件中的PPPoE数据包
"""

from scapy.all import rdpcap, Ether, PPPoE, PPPoED, IP, TCP, UDP, ICMP
from collections import Counter

def analyze_pcap(filename):
    print(f"正在分析文件: {filename}")
    print("=" * 80)
    
    packets = rdpcap(filename)
    print(f"\n总数据包数量: {len(packets)}\n")
    
    # 统计信息
    ether_types = Counter()
    mac_src = Counter()
    mac_dst = Counter()
    session_ids = Counter()
    protocols = Counter()
    
    pppoe_session_packets = []
    pppoe_discovery_packets = []
    
    for i, pkt in enumerate(packets):
        # 以太网类型统计
        if Ether in pkt:
            ether_type = pkt[Ether].type
            if ether_type == 0x8863:
                ether_types['PPPoE Discovery (0x8863)'] += 1
                pppoe_discovery_packets.append((i, pkt))
            elif ether_type == 0x8864:
                ether_types['PPPoE Session (0x8864)'] += 1
                pppoe_session_packets.append((i, pkt))
            else:
                ether_types[f'其他 (0x{ether_type:04x})'] += 1
            
            mac_src[pkt[Ether].src] += 1
            mac_dst[pkt[Ether].dst] += 1
        
        # PPPoE Session统计
        if PPPoE in pkt:
            session_ids[pkt[PPPoE].sessionid] += 1
            
            # 协议统计
            if IP in pkt:
                if TCP in pkt:
                    protocols['TCP'] += 1
                elif UDP in pkt:
                    protocols['UDP'] += 1
                elif ICMP in pkt:
                    protocols['ICMP'] += 1
                else:
                    protocols['其他IP协议'] += 1
    
    # 打印统计结果
    print("=" * 80)
    print("以太网类型分布")
    print("=" * 80)
    for etype, count in ether_types.most_common():
        print(f"  {etype}: {count} 个 ({count/len(packets)*100:.2f}%)")
    
    print("\n" + "=" * 80)
    print("MAC地址统计")
    print("=" * 80)
    print("\n源MAC地址:")
    for mac, count in mac_src.most_common():
        print(f"  {mac}: {count} 个")
    print("\n目标MAC地址:")
    for mac, count in mac_dst.most_common():
        print(f"  {mac}: {count} 个")
    
    print("\n" + "=" * 80)
    print("PPPoE Discovery阶段分析")
    print("=" * 80)
    if pppoe_discovery_packets:
        print(f"\n找到 {len(pppoe_discovery_packets)} 个PPPoE Discovery包!")
        for idx, (pkt_num, pkt) in enumerate(pppoe_discovery_packets[:10]):
            print(f"\n包 #{pkt_num + 1}:")
            if PPPoED in pkt:
                print(f"  Code: 0x{pkt[PPPoED].code:02x}")
                print(f"  Session ID: 0x{pkt[PPPoED].sessionid:04x}")
                print(f"  源MAC: {pkt[Ether].src}")
                print(f"  目标MAC: {pkt[Ether].dst}")
                pkt[PPPoED].show()
    else:
        print("\n⚠️  未找到PPPoE Discovery阶段的数据包")
        print("   原因: PPPoE连接在抓包前已建立")
    
    print("\n" + "=" * 80)
    print("PPPoE Session阶段分析")
    print("=" * 80)
    print(f"\nPPPoE Session包数量: {len(pppoe_session_packets)}")
    
    if session_ids:
        print("\nSession ID分布:")
        for sid, count in session_ids.most_common():
            print(f"  Session ID 0x{sid:04x} ({sid}): {count} 个包")
    
    if protocols:
        print("\n传输层协议分布:")
        for proto, count in protocols.most_common():
            print(f"  {proto}: {count} 个 ({count/len(pppoe_session_packets)*100:.2f}%)")
    
    # 显示典型的PPPoE Session包详情
    if pppoe_session_packets:
        print("\n" + "=" * 80)
        print("典型PPPoE Session包详细分析 (前3个)")
        print("=" * 80)
        
        for idx, (pkt_num, pkt) in enumerate(pppoe_session_packets[:3]):
            print(f"\n{'='*60}")
            print(f"包 #{pkt_num + 1}")
            print('='*60)
            
            # 以太网层
            if Ether in pkt:
                print("\n【以太网层】")
                print(f"  源MAC地址: {pkt[Ether].src}")
                print(f"  目标MAC地址: {pkt[Ether].dst}")
                print(f"  类型: 0x{pkt[Ether].type:04x} (PPPoE Session)")
            
            # PPPoE层
            if PPPoE in pkt:
                print("\n【PPPoE层】")
                print(f"  版本: {pkt[PPPoE].version}")
                print(f"  类型: {pkt[PPPoE].type}")
                print(f"  Code: {pkt[PPPoE].code}")
                print(f"  Session ID: 0x{pkt[PPPoE].sessionid:04x} ({pkt[PPPoE].sessionid})")
                print(f"  长度: {pkt[PPPoE].len} 字节")
            
            # IP层
            if IP in pkt:
                print("\n【IP层】")
                print(f"  源IP: {pkt[IP].src}")
                print(f"  目标IP: {pkt[IP].dst}")
                print(f"  协议: {pkt[IP].proto}")
                print(f"  TTL: {pkt[IP].ttl}")
                print(f"  总长度: {pkt[IP].len} 字节")
            
            # 传输层
            if TCP in pkt:
                print("\n【TCP层】")
                print(f"  源端口: {pkt[TCP].sport}")
                print(f"  目标端口: {pkt[TCP].dport}")
                print(f"  序列号: {pkt[TCP].seq}")
                print(f"  确认号: {pkt[TCP].ack}")
                print(f"  标志: {pkt[TCP].flags}")
            elif UDP in pkt:
                print("\n【UDP层】")
                print(f"  源端口: {pkt[UDP].sport}")
                print(f"  目标端口: {pkt[UDP].dport}")
                print(f"  长度: {pkt[UDP].len} 字节")
    
    print("\n" + "=" * 80)
    print("分析完成!")
    print("=" * 80)

if __name__ == "__main__":
    analyze_pcap("程泽凯.pcapng")
