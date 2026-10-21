#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细分析教务处网站访问流量
"""

from scapy.all import *
import binascii

def analyze_jwc_traffic(filename):
    """分析与教务处相关的流量"""
    print("="*80)
    print("教务处网站访问详细分析")
    print("="*80)
    
    packets = rdpcap(filename)
    jwc_ip = "202.115.71.132"  # 从之前的分析中发现的教务处IP
    
    # 查找所有与教务处相关的数据包
    jwc_packets = []
    for i, pkt in enumerate(packets):
        if pkt.haslayer(IP):
            if pkt[IP].src == jwc_ip or pkt[IP].dst == jwc_ip:
                jwc_packets.append((i+1, pkt))
    
    print(f"\n找到 {len(jwc_packets)} 个与教务处服务器相关的数据包")
    print(f"教务处服务器 IP: {jwc_ip}")
    print("="*80)
    
    # 分析 DNS 查询
    print("\n【DNS 查询】")
    print("-"*80)
    for i, pkt in enumerate(packets):
        if pkt.haslayer(DNS) and pkt[DNS].qr == 0:  # DNS 查询
            if pkt[DNS].qd and b'jwc' in bytes(pkt[DNS].qd.qname):
                print(f"\n数据包 #{i+1}:")
                print(f"  查询域名: {pkt[DNS].qd.qname.decode()}")
                print(f"  查询类型: {pkt[DNS].qd.qtype}")
                
    # 分析 DNS 响应
    print("\n【DNS 响应】")
    print("-"*80)
    for i, pkt in enumerate(packets):
        if pkt.haslayer(DNS) and pkt[DNS].qr == 1:  # DNS 响应
            if pkt[DNS].qd and b'jwc' in bytes(pkt[DNS].qd.qname):
                print(f"\n数据包 #{i+1}:")
                print(f"  域名: {pkt[DNS].qd.qname.decode()}")
                if pkt[DNS].an:
                    print(f"  解析结果:")
                    for j in range(pkt[DNS].ancount):
                        if pkt[DNS].an[j].type == 1:  # A 记录
                            print(f"    IP: {pkt[DNS].an[j].rdata}")
    
    # 分析 TCP 连接
    print("\n【TCP 连接分析】")
    print("-"*80)
    tcp_streams = {}
    for pkt_num, pkt in jwc_packets:
        if pkt.haslayer(TCP):
            src = pkt[IP].src
            dst = pkt[IP].dst
            sport = pkt[TCP].sport
            dport = pkt[TCP].dport
            flags = pkt[TCP].flags
            
            stream_key = f"{src}:{sport} <-> {dst}:{dport}"
            if stream_key not in tcp_streams:
                tcp_streams[stream_key] = []
            tcp_streams[stream_key].append((pkt_num, flags))
    
    for stream, packets_list in tcp_streams.items():
        print(f"\n流: {stream}")
        print(f"  数据包数量: {len(packets_list)}")
        print(f"  TCP 标志:")
        for pkt_num, flags in packets_list[:10]:  # 只显示前10个
            flag_str = ""
            if flags & 0x02: flag_str += "SYN "
            if flags & 0x10: flag_str += "ACK "
            if flags & 0x01: flag_str += "FIN "
            if flags & 0x04: flag_str += "RST "
            if flags & 0x08: flag_str += "PSH "
            print(f"    数据包 #{pkt_num}: {flag_str}")
    
    # 分析 HTTP/HTTPS 流量
    print("\n【HTTP/HTTPS 流量分析】")
    print("-"*80)
    
    http_packets = []
    https_packets = []
    
    for pkt_num, pkt in jwc_packets:
        if pkt.haslayer(TCP):
            if pkt[TCP].dport == 80 or pkt[TCP].sport == 80:
                http_packets.append((pkt_num, pkt))
            elif pkt[TCP].dport == 443 or pkt[TCP].sport == 443:
                https_packets.append((pkt_num, pkt))
    
    print(f"\nHTTP (端口 80) 数据包: {len(http_packets)} 个")
    print(f"HTTPS (端口 443) 数据包: {len(https_packets)} 个")
    
    # 详细分析前几个数据包
    print("\n【详细数据包分析】(前10个)")
    print("-"*80)
    for i, (pkt_num, pkt) in enumerate(jwc_packets[:10]):
        print(f"\n{'='*80}")
        print(f"数据包 #{pkt_num}")
        print(f"{'='*80}")
        
        if pkt.haslayer(IP):
            print(f"IP 层:")
            print(f"  源IP: {pkt[IP].src}")
            print(f"  目标IP: {pkt[IP].dst}")
            print(f"  协议: {pkt[IP].proto}")
            print(f"  TTL: {pkt[IP].ttl}")
            print(f"  长度: {pkt[IP].len}")
        
        if pkt.haslayer(TCP):
            print(f"TCP 层:")
            print(f"  源端口: {pkt[TCP].sport}")
            print(f"  目标端口: {pkt[TCP].dport}")
            print(f"  序列号: {pkt[TCP].seq}")
            print(f"  确认号: {pkt[TCP].ack}")
            flags = pkt[TCP].flags
            flag_str = ""
            if flags & 0x02: flag_str += "SYN "
            if flags & 0x10: flag_str += "ACK "
            if flags & 0x01: flag_str += "FIN "
            if flags & 0x04: flag_str += "RST "
            if flags & 0x08: flag_str += "PSH "
            print(f"  标志: {flag_str}")
            print(f"  窗口大小: {pkt[TCP].window}")
        
        if pkt.haslayer(Raw):
            raw_data = bytes(pkt[Raw].load)
            print(f"载荷数据:")
            print(f"  长度: {len(raw_data)} 字节")
            
            # 尝试解析 HTTP
            try:
                data_str = raw_data.decode('utf-8', errors='ignore')
                if 'HTTP' in data_str or 'GET' in data_str or 'POST' in data_str:
                    print(f"  HTTP 数据:")
                    print("  " + "\n  ".join(data_str[:500].split('\n')))
            except:
                pass
            
            # 显示十六进制
            print(f"  十六进制 (前64字节):")
            hex_str = binascii.hexlify(raw_data[:64]).decode()
            for j in range(0, len(hex_str), 32):
                print(f"    {hex_str[j:j+32]}")
    
    # 保存结果
    with open('教务处访问详细分析.txt', 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("教务处网站访问详细分析报告\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"教务处服务器 IP: {jwc_ip}\n")
        f.write(f"相关数据包总数: {len(jwc_packets)}\n")
        f.write(f"HTTP 数据包: {len(http_packets)}\n")
        f.write(f"HTTPS 数据包: {len(https_packets)}\n\n")
        
        f.write("【数据包列表】\n")
        f.write("-"*80 + "\n")
        for pkt_num, pkt in jwc_packets:
            if pkt.haslayer(IP) and pkt.haslayer(TCP):
                f.write(f"#{pkt_num:4d}: {pkt[IP].src:15s}:{pkt[TCP].sport:5d} -> "
                       f"{pkt[IP].dst:15s}:{pkt[TCP].dport:5d}\n")
    
    print("\n\n详细分析结果已保存到: 教务处访问详细分析.txt")

if __name__ == "__main__":
    analyze_jwc_traffic("2023112621.pcapng")
