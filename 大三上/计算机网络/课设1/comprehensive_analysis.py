#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2023112621.pcapng 综合分析脚本
全面分析网络流量，包括协议分布、连接信息、关键数据等
"""

from scapy.all import *
from collections import defaultdict, Counter
import json

def analyze_pcap(filename):
    """综合分析 pcap 文件"""
    print(f"正在读取文件: {filename}")
    packets = rdpcap(filename)
    print(f"总数据包数量: {len(packets)}")
    print("="*80)
    
    # 统计信息
    protocol_stats = Counter()
    ip_conversations = defaultdict(int)
    tcp_ports = defaultdict(int)
    udp_ports = defaultdict(int)
    http_requests = []
    dns_queries = []
    pppoe_packets = []
    
    # 分析每个数据包
    for i, pkt in enumerate(packets):
        # 协议统计
        if pkt.haslayer(Ether):
            protocol_stats['Ethernet'] += 1
            
        if pkt.haslayer(PPPoE):
            protocol_stats['PPPoE'] += 1
            pppoe_packets.append((i+1, pkt))
            
        if pkt.haslayer(IP):
            protocol_stats['IP'] += 1
            src = pkt[IP].src
            dst = pkt[IP].dst
            ip_conversations[f"{src} -> {dst}"] += 1
            
        if pkt.haslayer(TCP):
            protocol_stats['TCP'] += 1
            tcp_ports[pkt[TCP].sport] += 1
            tcp_ports[pkt[TCP].dport] += 1
            
        if pkt.haslayer(UDP):
            protocol_stats['UDP'] += 1
            udp_ports[pkt[UDP].sport] += 1
            udp_ports[pkt[UDP].dport] += 1
            
        if pkt.haslayer(DNS):
            protocol_stats['DNS'] += 1
            if pkt[DNS].qr == 0:  # DNS 查询
                if pkt[DNS].qd:
                    dns_queries.append({
                        'packet': i+1,
                        'query': pkt[DNS].qd.qname.decode() if pkt[DNS].qd.qname else 'N/A'
                    })
                    
        if pkt.haslayer(Raw):
            raw_data = bytes(pkt[Raw].load)
            # 检测 HTTP 请求
            if raw_data.startswith(b'GET ') or raw_data.startswith(b'POST ') or raw_data.startswith(b'HTTP/'):
                try:
                    data_str = raw_data.decode('utf-8', errors='ignore')
                    http_requests.append({
                        'packet': i+1,
                        'data': data_str[:200]  # 只保存前200字符
                    })
                except:
                    pass
    
    # 输出分析结果
    print("\n" + "="*80)
    print("【1. 协议分布统计】")
    print("="*80)
    for proto, count in protocol_stats.most_common():
        percentage = (count / len(packets)) * 100
        print(f"{proto:15s}: {count:6d} 个数据包 ({percentage:.2f}%)")
    
    print("\n" + "="*80)
    print("【2. IP 通信统计】(前20个最频繁的通信)")
    print("="*80)
    for conv, count in sorted(ip_conversations.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"{conv:50s}: {count:5d} 个数据包")
    
    print("\n" + "="*80)
    print("【3. TCP 端口统计】(前20个最活跃的端口)")
    print("="*80)
    for port, count in sorted(tcp_ports.items(), key=lambda x: x[1], reverse=True)[:20]:
        port_name = get_port_name(port)
        print(f"端口 {port:5d} ({port_name:15s}): {count:5d} 次")
    
    print("\n" + "="*80)
    print("【4. UDP 端口统计】(前20个最活跃的端口)")
    print("="*80)
    for port, count in sorted(udp_ports.items(), key=lambda x: x[1], reverse=True)[:20]:
        port_name = get_port_name(port)
        print(f"端口 {port:5d} ({port_name:15s}): {count:5d} 次")
    
    print("\n" + "="*80)
    print("【5. DNS 查询记录】(前30个)")
    print("="*80)
    for i, query in enumerate(dns_queries[:30], 1):
        print(f"{i:3d}. 数据包 #{query['packet']:5d}: {query['query']}")
    
    print("\n" + "="*80)
    print("【6. HTTP 请求/响应】(前20个)")
    print("="*80)
    for i, req in enumerate(http_requests[:20], 1):
        print(f"\n--- HTTP 数据包 #{req['packet']} ---")
        print(req['data'])
    
    print("\n" + "="*80)
    print("【7. PPPoE 数据包分析】")
    print("="*80)
    print(f"PPPoE 数据包总数: {len(pppoe_packets)}")
    
    if pppoe_packets:
        print("\n前10个 PPPoE 数据包详情:")
        for i, (pkt_num, pkt) in enumerate(pppoe_packets[:10], 1):
            print(f"\n--- PPPoE 数据包 #{pkt_num} ---")
            if pkt.haslayer(PPPoE):
                pppoe = pkt[PPPoE]
                print(f"  版本: {pppoe.version}")
                print(f"  类型: {pppoe.type}")
                print(f"  代码: {pppoe.code}")
                print(f"  会话ID: {pppoe.sessionid}")
                print(f"  长度: {pppoe.len}")
    
    # 详细分析特定数据包
    print("\n" + "="*80)
    print("【8. 关键数据包详细分析】")
    print("="*80)
    
    # 分析前几个数据包
    for i in range(min(5, len(packets))):
        print(f"\n{'='*80}")
        print(f"数据包 #{i+1}")
        print(f"{'='*80}")
        packets[i].show()
    
    # 保存详细结果到文件
    save_detailed_results(packets, protocol_stats, ip_conversations, 
                         tcp_ports, udp_ports, dns_queries, http_requests, pppoe_packets)
    
    return packets

def get_port_name(port):
    """获取端口对应的服务名称"""
    port_names = {
        20: 'FTP-DATA',
        21: 'FTP',
        22: 'SSH',
        23: 'Telnet',
        25: 'SMTP',
        53: 'DNS',
        67: 'DHCP-Server',
        68: 'DHCP-Client',
        80: 'HTTP',
        110: 'POP3',
        143: 'IMAP',
        443: 'HTTPS',
        3389: 'RDP',
        8080: 'HTTP-Proxy',
    }
    return port_names.get(port, 'Unknown')

def save_detailed_results(packets, protocol_stats, ip_conversations, 
                         tcp_ports, udp_ports, dns_queries, http_requests, pppoe_packets):
    """保存详细分析结果到文件"""
    with open('综合分析报告.txt', 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("2023112621.pcapng 综合分析报告\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"总数据包数量: {len(packets)}\n\n")
        
        f.write("【协议分布】\n")
        f.write("-"*80 + "\n")
        for proto, count in protocol_stats.most_common():
            percentage = (count / len(packets)) * 100
            f.write(f"{proto:15s}: {count:6d} ({percentage:.2f}%)\n")
        
        f.write("\n【IP 通信统计】\n")
        f.write("-"*80 + "\n")
        for conv, count in sorted(ip_conversations.items(), key=lambda x: x[1], reverse=True)[:50]:
            f.write(f"{conv:50s}: {count:5d}\n")
        
        f.write("\n【DNS 查询】\n")
        f.write("-"*80 + "\n")
        for query in dns_queries:
            f.write(f"数据包 #{query['packet']:5d}: {query['query']}\n")
        
        f.write("\n【HTTP 请求/响应】\n")
        f.write("-"*80 + "\n")
        for req in http_requests:
            f.write(f"\n--- 数据包 #{req['packet']} ---\n")
            f.write(req['data'] + "\n")
        
        f.write("\n【PPPoE 数据包】\n")
        f.write("-"*80 + "\n")
        f.write(f"总数: {len(pppoe_packets)}\n")
        for pkt_num, pkt in pppoe_packets[:50]:
            f.write(f"\n数据包 #{pkt_num}:\n")
            if pkt.haslayer(PPPoE):
                pppoe = pkt[PPPoE]
                f.write(f"  会话ID: {pppoe.sessionid}, 代码: {pppoe.code}\n")
    
    print("\n详细分析结果已保存到: 综合分析报告.txt")

if __name__ == "__main__":
    analyze_pcap("2023112621.pcapng")
