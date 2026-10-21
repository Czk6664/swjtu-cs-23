#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成详细的PPPoE分析报告
包含数据包序号、阶段划分、协议分析等
"""

import sys
from collections import Counter, defaultdict

try:
    from scapy.all import rdpcap, Ether, IP, TCP, UDP, ICMP, DNS, Raw
    from scapy.layers.ppp import PPPoE, PPPoED
except ImportError as e:
    print(f"错误: 需要安装 scapy 库")
    sys.exit(1)

def format_hex_dump(data, max_bytes=256):
    """格式化十六进制输出"""
    lines = []
    for i in range(0, min(len(data), max_bytes), 16):
        hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        lines.append(f"  {i:04x}: {hex_part:<48} {ascii_part}")
    return '\n'.join(lines)

def analyze_stages_detailed(packets):
    """详细分析各个阶段并输出报文序号"""
    
    stages = {
        'DNS查询': [],
        'DNS响应': [],
        'TCP SYN': [],
        'TCP SYN-ACK': [],
        'TCP ACK': [],
        'TLS握手': [],
        'HTTP/HTTPS数据': [],
        'ICMP': []
    }
    
    print("\n" + "=" * 80)
    print("详细阶段分析 - 按报文序号")
    print("=" * 80)
    
    for i, pkt in enumerate(packets):
        pkt_num = i + 1
        
        # DNS分析
        if DNS in pkt:
            if pkt[DNS].qr == 0:  # Query
                qname = pkt[DNS].qd.qname.decode() if pkt[DNS].qd else 'Unknown'
                stages['DNS查询'].append({
                    'num': pkt_num,
                    'query': qname,
                    'src': pkt[IP].src if IP in pkt else 'N/A',
                    'dst': pkt[IP].dst if IP in pkt else 'N/A'
                })
            else:  # Response
                stages['DNS响应'].append({
                    'num': pkt_num,
                    'src': pkt[IP].src if IP in pkt else 'N/A',
                    'dst': pkt[IP].dst if IP in pkt else 'N/A'
                })
        
        # TCP分析
        if TCP in pkt:
            flags = pkt[TCP].flags
            src = f"{pkt[IP].src}:{pkt[TCP].sport}" if IP in pkt else 'N/A'
            dst = f"{pkt[IP].dst}:{pkt[TCP].dport}" if IP in pkt else 'N/A'
            
            if flags & 0x02:  # SYN
                if flags & 0x10:  # SYN-ACK
                    stages['TCP SYN-ACK'].append({
                        'num': pkt_num,
                        'src': src,
                        'dst': dst
                    })
                else:
                    stages['TCP SYN'].append({
                        'num': pkt_num,
                        'src': src,
                        'dst': dst
                    })
            elif flags & 0x10 and not (flags & 0x02):  # Pure ACK
                # 只记录前几个ACK
                if len(stages['TCP ACK']) < 20:
                    stages['TCP ACK'].append({
                        'num': pkt_num,
                        'src': src,
                        'dst': dst
                    })
        
        # TLS/SSL分析
        if Raw in pkt and TCP in pkt:
            payload = bytes(pkt[Raw].load)
            # TLS握手报文以 0x16 开头
            if len(payload) > 0 and payload[0] == 0x16:
                if len(stages['TLS握手']) < 20:
                    stages['TLS握手'].append({
                        'num': pkt_num,
                        'src': f"{pkt[IP].src}:{pkt[TCP].sport}" if IP in pkt else 'N/A',
                        'dst': f"{pkt[IP].dst}:{pkt[TCP].dport}" if IP in pkt else 'N/A',
                        'len': len(payload)
                    })
        
        # ICMP分析
        if ICMP in pkt:
            stages['ICMP'].append({
                'num': pkt_num,
                'type': pkt[ICMP].type,
                'src': pkt[IP].src if IP in pkt else 'N/A',
                'dst': pkt[IP].dst if IP in pkt else 'N/A'
            })
    
    # 输出各阶段详细信息
    print("\n【阶段1: DNS解析阶段】")
    print("-" * 80)
    print(f"DNS查询报文数量: {len(stages['DNS查询'])}")
    print(f"DNS响应报文数量: {len(stages['DNS响应'])}")
    
    if stages['DNS查询']:
        print("\nDNS查询详情(前10个):")
        for item in stages['DNS查询'][:10]:
            print(f"  报文#{item['num']:4d}: {item['src']} -> {item['dst']}")
            print(f"           查询域名: {item['query']}")
    
    if stages['DNS响应']:
        print("\nDNS响应详情(前10个):")
        for item in stages['DNS响应'][:10]:
            print(f"  报文#{item['num']:4d}: {item['src']} -> {item['dst']}")
    
    print("\n【阶段2: TCP连接建立阶段】")
    print("-" * 80)
    print(f"TCP SYN报文数量: {len(stages['TCP SYN'])}")
    print(f"TCP SYN-ACK报文数量: {len(stages['TCP SYN-ACK'])}")
    
    if stages['TCP SYN']:
        print("\nTCP SYN报文详情(前10个):")
        for item in stages['TCP SYN'][:10]:
            print(f"  报文#{item['num']:4d}: {item['src']} -> {item['dst']}")
    
    if stages['TCP SYN-ACK']:
        print("\nTCP SYN-ACK报文详情(前10个):")
        for item in stages['TCP SYN-ACK'][:10]:
            print(f"  报文#{item['num']:4d}: {item['src']} -> {item['dst']}")
    
    print("\n【阶段3: TLS/SSL握手阶段】")
    print("-" * 80)
    print(f"TLS握手报文数量: {len(stages['TLS握手'])}")
    
    if stages['TLS握手']:
        print("\nTLS握手报文详情(前10个):")
        for item in stages['TLS握手'][:10]:
            print(f"  报文#{item['num']:4d}: {item['src']} -> {item['dst']} (长度: {item['len']} 字节)")
    
    return stages

def analyze_login_packets(packets):
    """分析可能包含登录信息的数据包"""
    
    print("\n" + "=" * 80)
    print("登录相关数据包分析")
    print("=" * 80)
    
    login_keywords = [
        b'username', b'password', b'user', b'pass', b'login',
        b'account', b'userid', b'passwd', b'pwd'
    ]
    
    suspicious_packets = []
    
    for i, pkt in enumerate(packets):
        if Raw in pkt and TCP in pkt:
            payload = bytes(pkt[Raw].load)
            
            # 检查是否包含登录关键字
            for keyword in login_keywords:
                if keyword in payload.lower():
                    suspicious_packets.append({
                        'num': i + 1,
                        'src': f"{pkt[IP].src}:{pkt[TCP].sport}" if IP in pkt else 'N/A',
                        'dst': f"{pkt[IP].dst}:{pkt[TCP].dport}" if IP in pkt else 'N/A',
                        'payload': payload,
                        'keyword': keyword.decode()
                    })
                    break
    
    if suspicious_packets:
        print(f"\n发现 {len(suspicious_packets)} 个可能包含登录信息的数据包\n")
        
        for item in suspicious_packets[:5]:
            print(f"【报文 #{item['num']}】")
            print(f"源地址: {item['src']}")
            print(f"目的地址: {item['dst']}")
            print(f"匹配关键字: {item['keyword']}")
            print(f"负载长度: {len(item['payload'])} 字节")
            
            # 检查是否为TLS加密
            if len(item['payload']) > 0 and item['payload'][0] == 0x16:
                print("类型: TLS加密数据 (无法读取明文)")
            else:
                print("类型: 可能包含明文数据")
            
            print("\n十六进制内容(前128字节):")
            print(format_hex_dump(item['payload'], 128))
            
            # 尝试解码可读部分
            try:
                readable = item['payload'].decode('utf-8', errors='ignore')
                if readable.strip():
                    print("\n可读文本(前200字符):")
                    print(f"  {readable[:200]}")
            except:
                pass
            
            print("\n" + "-" * 80)
    else:
        print("\n未发现包含登录关键字的数据包")
    
    # 特别分析HTTPS连接
    print("\n【HTTPS连接分析】")
    print("-" * 80)
    
    https_connections = []
    for i, pkt in enumerate(packets):
        if TCP in pkt and pkt[TCP].dport == 443:
            if Raw in pkt:
                payload = bytes(pkt[Raw].load)
                if len(payload) > 0 and payload[0] == 0x16:  # TLS
                    # 尝试提取SNI (Server Name Indication)
                    if b'login' in payload or b'jwc' in payload:
                        https_connections.append({
                            'num': i + 1,
                            'src': f"{pkt[IP].src}:{pkt[TCP].sport}" if IP in pkt else 'N/A',
                            'dst': f"{pkt[IP].dst}:{pkt[TCP].dport}" if IP in pkt else 'N/A',
                            'payload': payload
                        })
    
    if https_connections:
        print(f"\n发现 {len(https_connections)} 个可能相关的HTTPS连接\n")
        for item in https_connections[:3]:
            print(f"【报文 #{item['num']}】")
            print(f"连接: {item['src']} -> {item['dst']}")
            print("说明: HTTPS加密连接,登录数据在加密通道中传输")
            print("安全性: 无法通过抓包获取明文用户名和密码")
            print()

def main():
    filename = "ppoe.pcapng"
    
    print("=" * 80)
    print("PPPoE 数据包详细分析报告")
    print("=" * 80)
    print(f"分析文件: {filename}\n")
    
    try:
        packets = rdpcap(filename)
        print(f"成功读取 {len(packets)} 个数据包\n")
    except Exception as e:
        print(f"读取文件失败: {e}")
        return
    
    # 基本统计
    print("=" * 80)
    print("基本统计信息")
    print("=" * 80)
    
    protocol_stats = Counter()
    for pkt in packets:
        if TCP in pkt:
            protocol_stats['TCP'] += 1
        if UDP in pkt:
            protocol_stats['UDP'] += 1
        if DNS in pkt:
            protocol_stats['DNS'] += 1
        if ICMP in pkt:
            protocol_stats['ICMP'] += 1
    
    print("\n协议分布:")
    for proto, count in protocol_stats.most_common():
        percentage = (count / len(packets)) * 100
        print(f"  {proto:10s}: {count:5d} 个 ({percentage:5.2f}%)")
    
    # 详细阶段分析
    stages = analyze_stages_detailed(packets)
    
    # 登录信息分析
    analyze_login_packets(packets)
    
    print("\n" + "=" * 80)
    print("分析完成!")
    print("=" * 80)
    print("\n报告已生成,详细内容请查看: PPPoE分析报告.md")

if __name__ == "__main__":
    main()
