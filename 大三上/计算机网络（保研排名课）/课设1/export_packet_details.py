#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出关键数据包的详细信息,用于报告中的图示
"""

from scapy.all import *
from scapy.layers.ppp import *
from scapy.layers.l2 import Ether
import struct

def export_packet_hex(pkt, pkt_num, description):
    """导出数据包的十六进制表示"""
    print(f"\n{'='*80}")
    print(f"数据包 #{pkt_num}: {description}")
    print(f"{'='*80}")
    
    # 基本信息
    print(f"\n【基本信息】")
    print(f"数据包长度: {len(pkt)} 字节")
    if hasattr(pkt, 'time'):
        print(f"时间戳: {pkt.time}")
    
    # 协议栈
    print(f"\n【协议栈】")
    layers = []
    layer = pkt
    while layer:
        layers.append(layer.name)
        layer = layer.payload if hasattr(layer, 'payload') else None
    print(" / ".join(layers))
    
    # 以太网层
    if Ether in pkt:
        print(f"\n【以太网层】")
        print(f"目标MAC: {pkt[Ether].dst}")
        print(f"源MAC: {pkt[Ether].src}")
        print(f"类型: 0x{pkt[Ether].type:04x}")
    
    # PPPoE层
    raw_bytes = bytes(pkt)
    if len(raw_bytes) > 14:
        eth_header_len = 14
        if len(raw_bytes) > eth_header_len + 6:
            pppoe_header = raw_bytes[eth_header_len:eth_header_len+6]
            version_type = pppoe_header[0]
            version = (version_type >> 4) & 0x0F
            type_val = version_type & 0x0F
            code = pppoe_header[1]
            session_id = struct.unpack('!H', pppoe_header[2:4])[0]
            length = struct.unpack('!H', pppoe_header[4:6])[0]
            
            print(f"\n【PPPoE层】")
            print(f"版本: {version}")
            print(f"类型: {type_val}")
            print(f"代码: 0x{code:02x}")
            print(f"会话ID: 0x{session_id:04x} ({session_id})")
            print(f"长度: {length} 字节")
    
    # IP层
    if IP in pkt:
        print(f"\n【IP层】")
        print(f"源IP: {pkt[IP].src}")
        print(f"目标IP: {pkt[IP].dst}")
        print(f"协议: {pkt[IP].proto}")
        print(f"TTL: {pkt[IP].ttl}")
        print(f"总长度: {pkt[IP].len}")
    
    # TCP层
    if TCP in pkt:
        print(f"\n【TCP层】")
        print(f"源端口: {pkt[TCP].sport}")
        print(f"目标端口: {pkt[TCP].dport}")
        print(f"序列号: {pkt[TCP].seq}")
        print(f"确认号: {pkt[TCP].ack}")
        print(f"标志位: {pkt[TCP].flags}")
        print(f"窗口大小: {pkt[TCP].window}")
    
    # UDP层
    if UDP in pkt:
        print(f"\n【UDP层】")
        print(f"源端口: {pkt[UDP].sport}")
        print(f"目标端口: {pkt[UDP].dport}")
        print(f"长度: {pkt[UDP].len}")
    
    # DNS层
    if DNS in pkt:
        print(f"\n【DNS层】")
        print(f"查询数: {pkt[DNS].qdcount}")
        print(f"应答数: {pkt[DNS].ancount}")
        if pkt[DNS].qd:
            qname = pkt[DNS].qd.qname
            query = qname.decode() if isinstance(qname, bytes) else str(qname)
            print(f"查询域名: {query}")
        if pkt[DNS].an:
            print(f"应答记录:")
            for i in range(pkt[DNS].ancount):
                try:
                    if pkt[DNS].an[i].type == 1:
                        print(f"  - {pkt[DNS].an[i].rdata}")
                except:
                    pass
    
    # 十六进制dump
    print(f"\n【十六进制数据】")
    hex_data = raw_bytes.hex()
    
    # 按行显示,每行16字节(32个十六进制字符)
    offset = 0
    bytes_per_line = 16
    
    for i in range(0, len(raw_bytes), bytes_per_line):
        # 十六进制部分
        hex_part = ' '.join([hex_data[j:j+2] for j in range(i*2, min((i+bytes_per_line)*2, len(hex_data)), 2)])
        
        # ASCII部分
        ascii_part = ''
        for j in range(i, min(i+bytes_per_line, len(raw_bytes))):
            byte = raw_bytes[j]
            if 32 <= byte <= 126:
                ascii_part += chr(byte)
            else:
                ascii_part += '.'
        
        print(f"{offset:04x}  {hex_part:<48}  {ascii_part}")
        offset += bytes_per_line
    
    # 如果有Raw层,显示载荷
    if Raw in pkt:
        payload = bytes(pkt[Raw].load)
        if len(payload) > 0:
            print(f"\n【载荷数据】")
            print(f"载荷长度: {len(payload)} 字节")
            
            # 检查是否是TLS数据
            if len(payload) > 0:
                first_byte = payload[0]
                if first_byte == 0x16:
                    print(f"TLS记录类型: 0x16 (Handshake)")
                    if len(payload) >= 6:
                        handshake_type = payload[5]
                        tls_types = {
                            0x01: 'Client Hello',
                            0x02: 'Server Hello',
                            0x0b: 'Certificate',
                            0x0c: 'Server Key Exchange',
                            0x0e: 'Server Hello Done',
                            0x10: 'Client Key Exchange',
                            0x14: 'Finished'
                        }
                        print(f"TLS握手类型: {tls_types.get(handshake_type, f'Unknown (0x{handshake_type:02x})')}")
                elif first_byte == 0x17:
                    print(f"TLS记录类型: 0x17 (Application Data - 加密数据)")
                elif first_byte == 0x14:
                    print(f"TLS记录类型: 0x14 (Change Cipher Spec)")
                elif first_byte == 0x15:
                    print(f"TLS记录类型: 0x15 (Alert)")

def main():
    pcap_file = r'd:\桌面\计算机网络\课设1\程泽凯.pcapng'
    
    print("="*80)
    print("关键数据包详细信息导出")
    print("="*80)
    
    packets = rdpcap(pcap_file)
    
    # 选择关键数据包进行详细展示
    key_packets = [
        (1, "PPPoE Session - HTTPS通信"),
        (140, "TCP三次握手 - SYN包"),
        (145, "TCP三次握手 - SYN-ACK包"),
        (146, "TCP三次握手 - ACK包"),
        (147, "TLS握手 - Client Hello"),
        (151, "TLS握手 - Server Hello"),
        (254, "DNS查询"),
        (255, "DNS响应"),
        (292, "连接教务相关服务器 - SYN"),
        (293, "连接教务相关服务器 - SYN-ACK"),
        (295, "TLS握手 - Client Hello (教务服务器)"),
        (303, "TLS握手 - Server Hello (教务服务器)"),
    ]
    
    for pkt_num, description in key_packets:
        if pkt_num <= len(packets):
            export_packet_hex(packets[pkt_num-1], pkt_num, description)
    
    print("\n" + "="*80)
    print("导出完成!")
    print("="*80)
    print("\n提示: 你可以将上述输出复制到报告中,或者截图Wireshark中对应的数据包")
    print("在Wireshark中查看数据包的方法:")
    print("1. 打开 程泽凯.pcapng 文件")
    print("2. 在过滤器中输入: frame.number == 数据包序号")
    print("3. 右键点击数据包 -> Follow -> TCP Stream (查看TCP流)")
    print("4. 查看数据包详情面板,展开各层协议")

if __name__ == '__main__':
    main()
