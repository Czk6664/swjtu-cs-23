#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教务处网站访问数据包分析脚本
分析 程泽凯.pcapng 文件中的HTTP/HTTPS流量和登录信息
"""

from scapy.all import *
from scapy.layers.ppp import *
from scapy.layers.l2 import Ether
from collections import defaultdict, Counter
import json

def analyze_jwc_packets(pcap_file):
    """分析教务处网站访问的数据包"""
    
    print("="*80)
    print("教务处网站访问数据包分析")
    print("="*80)
    print(f"\n正在读取文件: {pcap_file}")
    
    try:
        packets = rdpcap(pcap_file)
        total_packets = len(packets)
        print(f"✓ 成功读取 {total_packets} 个数据包\n")
    except Exception as e:
        print(f"✗ 读取文件失败: {e}")
        return
    
    # 数据统计
    dns_queries = []
    http_packets = []
    https_packets = []
    tcp_streams = defaultdict(list)
    udp_packets = []
    
    # 阶段划分
    stages = {
        'DNS解析': [],
        'TCP连接建立': [],
        'TLS握手': [],
        'HTTP/HTTPS数据传输': [],
        '其他': []
    }
    
    print("="*80)
    print("开始逐包分析...")
    print("="*80)
    
    for idx, pkt in enumerate(packets, 1):
        pkt_info = {
            'num': idx,
            'time': float(pkt.time) if hasattr(pkt, 'time') else 0,
            'length': len(pkt)
        }
        
        # 提取以太网层信息
        if Ether in pkt:
            pkt_info['src_mac'] = pkt[Ether].src
            pkt_info['dst_mac'] = pkt[Ether].dst
            pkt_info['eth_type'] = hex(pkt[Ether].type)
        
        # 检查是否有IP层
        if IP in pkt:
            pkt_info['src_ip'] = pkt[IP].src
            pkt_info['dst_ip'] = pkt[IP].dst
            pkt_info['protocol'] = pkt[IP].proto
            
            # DNS分析
            if UDP in pkt and (pkt[UDP].sport == 53 or pkt[UDP].dport == 53):
                if DNS in pkt:
                    dns_info = pkt_info.copy()
                    dns_info['dns_type'] = 'Query' if pkt[UDP].dport == 53 else 'Response'
                    if pkt[DNS].qd:
                        dns_info['query'] = pkt[DNS].qd.qname.decode() if isinstance(pkt[DNS].qd.qname, bytes) else str(pkt[DNS].qd.qname)
                    if pkt[DNS].an:
                        dns_info['answers'] = []
                        for i in range(pkt[DNS].ancount):
                            if pkt[DNS].an[i].type == 1:  # A记录
                                dns_info['answers'].append(pkt[DNS].an[i].rdata)
                    dns_queries.append(dns_info)
                    stages['DNS解析'].append(idx)
            
            # TCP分析
            if TCP in pkt:
                tcp_info = pkt_info.copy()
                tcp_info['src_port'] = pkt[TCP].sport
                tcp_info['dst_port'] = pkt[TCP].dport
                tcp_info['flags'] = pkt[TCP].flags
                tcp_info['seq'] = pkt[TCP].seq
                tcp_info['ack'] = pkt[TCP].ack
                
                # 识别TCP连接建立(三次握手)
                if pkt[TCP].flags == 'S':  # SYN
                    stages['TCP连接建立'].append(idx)
                elif pkt[TCP].flags == 'SA':  # SYN-ACK
                    stages['TCP连接建立'].append(idx)
                elif pkt[TCP].flags == 'A' and len(pkt[TCP].payload) == 0:
                    # 可能是握手的第三个包
                    if idx - 1 in stages['TCP连接建立']:
                        stages['TCP连接建立'].append(idx)
                
                # HTTPS流量 (端口443)
                if pkt[TCP].dport == 443 or pkt[TCP].sport == 443:
                    https_packets.append(tcp_info)
                    
                    # 检查TLS握手
                    if Raw in pkt:
                        payload = bytes(pkt[Raw].load)
                        # TLS握手记录类型: 0x16
                        if len(payload) > 0 and payload[0] == 0x16:
                            stages['TLS握手'].append(idx)
                        else:
                            stages['HTTP/HTTPS数据传输'].append(idx)
                
                # HTTP流量 (端口80)
                elif pkt[TCP].dport == 80 or pkt[TCP].sport == 80:
                    if Raw in pkt:
                        payload = bytes(pkt[Raw].load)
                        try:
                            payload_str = payload.decode('utf-8', errors='ignore')
                            tcp_info['http_payload'] = payload_str[:500]  # 前500字符
                            
                            # 检查HTTP方法
                            if any(payload_str.startswith(method) for method in ['GET', 'POST', 'HEAD', 'PUT']):
                                tcp_info['http_method'] = payload_str.split()[0]
                                if len(payload_str.split()) > 1:
                                    tcp_info['http_uri'] = payload_str.split()[1]
                            
                            # 检查HTTP响应
                            if payload_str.startswith('HTTP/'):
                                tcp_info['http_response'] = payload_str.split('\r\n')[0]
                            
                            http_packets.append(tcp_info)
                            stages['HTTP/HTTPS数据传输'].append(idx)
                        except:
                            pass
                
                # 构建TCP流
                stream_key = f"{tcp_info['src_ip']}:{tcp_info['src_port']}->{tcp_info['dst_ip']}:{tcp_info['dst_port']}"
                tcp_streams[stream_key].append(tcp_info)
            
            # UDP分析
            elif UDP in pkt:
                udp_info = pkt_info.copy()
                udp_info['src_port'] = pkt[UDP].sport
                udp_info['dst_port'] = pkt[UDP].dport
                udp_packets.append(udp_info)
                
                if pkt[UDP].sport != 53 and pkt[UDP].dport != 53:
                    stages['其他'].append(idx)
        else:
            stages['其他'].append(idx)
    
    # 输出分析结果
    print("\n" + "="*80)
    print("一、数据包捕获概览")
    print("="*80)
    print(f"总数据包数: {total_packets}")
    print(f"DNS查询/响应: {len(dns_queries)}")
    print(f"HTTP数据包: {len(http_packets)}")
    print(f"HTTPS数据包: {len(https_packets)}")
    print(f"TCP流数量: {len(tcp_streams)}")
    
    # DNS查询分析
    if dns_queries:
        print("\n" + "="*80)
        print("DNS查询详情")
        print("="*80)
        for dns in dns_queries[:20]:  # 显示前20个
            print(f"\n包 #{dns['num']}:")
            print(f"  类型: {dns.get('dns_type', 'Unknown')}")
            if 'query' in dns:
                print(f"  查询域名: {dns['query']}")
            if 'answers' in dns:
                print(f"  解析结果: {', '.join(dns['answers'])}")
    
    # 阶段分析
    print("\n" + "="*80)
    print("二、访问Web网站的阶段划分")
    print("="*80)
    
    stage_order = ['DNS解析', 'TCP连接建立', 'TLS握手', 'HTTP/HTTPS数据传输', '其他']
    for stage_name in stage_order:
        pkts = stages[stage_name]
        if pkts:
            print(f"\n【{stage_name}】")
            print(f"  包含数据包数量: {len(pkts)}")
            print(f"  数据包序号: {pkts[:30]}")  # 显示前30个
            if len(pkts) > 30:
                print(f"  ... (还有 {len(pkts)-30} 个)")
    
    # HTTP详细分析
    if http_packets:
        print("\n" + "="*80)
        print("HTTP流量详细分析")
        print("="*80)
        for http in http_packets[:10]:
            print(f"\n包 #{http['num']}:")
            print(f"  {http['src_ip']}:{http['src_port']} -> {http['dst_ip']}:{http['dst_port']}")
            if 'http_method' in http:
                print(f"  HTTP方法: {http['http_method']}")
            if 'http_uri' in http:
                print(f"  请求URI: {http['http_uri']}")
            if 'http_response' in http:
                print(f"  响应: {http['http_response']}")
            if 'http_payload' in http:
                print(f"  载荷预览: {http['http_payload'][:200]}")
    
    # 查找可能的登录信息
    print("\n" + "="*80)
    print("三、登录信息分析")
    print("="*80)
    print("正在搜索可能包含用户名/密码的数据包...")
    
    login_keywords = ['username', 'password', 'user', 'pass', 'login', 'account', 
                      'userid', 'passwd', '用户名', '密码', '登录']
    
    potential_login_packets = []
    
    for idx, pkt in enumerate(packets, 1):
        if Raw in pkt:
            try:
                payload = bytes(pkt[Raw].load)
                payload_str = payload.decode('utf-8', errors='ignore').lower()
                
                # 检查是否包含登录关键词
                if any(keyword in payload_str for keyword in login_keywords):
                    info = {
                        'num': idx,
                        'length': len(payload),
                        'payload_hex': payload.hex(),
                        'payload_str': payload_str[:500]
                    }
                    
                    if IP in pkt:
                        info['src_ip'] = pkt[IP].src
                        info['dst_ip'] = pkt[IP].dst
                    
                    if TCP in pkt:
                        info['src_port'] = pkt[TCP].sport
                        info['dst_port'] = pkt[TCP].dport
                    
                    potential_login_packets.append(info)
            except:
                pass
    
    if potential_login_packets:
        print(f"\n找到 {len(potential_login_packets)} 个可能包含登录信息的数据包:")
        for login_pkt in potential_login_packets[:10]:
            print(f"\n包 #{login_pkt['num']}:")
            if 'src_ip' in login_pkt:
                print(f"  源地址: {login_pkt['src_ip']}:{login_pkt.get('src_port', 'N/A')}")
                print(f"  目标地址: {login_pkt['dst_ip']}:{login_pkt.get('dst_port', 'N/A')}")
            print(f"  载荷长度: {login_pkt['length']} 字节")
            print(f"  载荷内容(文本): {login_pkt['payload_str'][:300]}")
            print(f"  载荷内容(十六进制前100字节): {login_pkt['payload_hex'][:200]}")
    else:
        print("\n⚠ 未找到明文的用户名/密码信息")
        print("可能原因:")
        print("  1. 使用了HTTPS加密传输(端口443)")
        print("  2. 使用了其他加密方式")
        print("  3. 登录信息已被编码或加密")
    
    # 详细分析HTTPS流量
    if https_packets:
        print("\n" + "="*80)
        print("HTTPS加密流量分析")
        print("="*80)
        print(f"HTTPS数据包总数: {len(https_packets)}")
        
        # 统计目标服务器
        https_servers = Counter()
        for pkt in https_packets:
            if pkt['dst_port'] == 443:
                https_servers[pkt['dst_ip']] += 1
            else:
                https_servers[pkt['src_ip']] += 1
        
        print("\nHTTPS连接的服务器:")
        for server, count in https_servers.most_common(10):
            print(f"  {server}: {count} 个数据包")
    
    # 生成详细报告
    print("\n" + "="*80)
    print("生成详细分析报告...")
    print("="*80)
    
    report = {
        '总数据包数': total_packets,
        'DNS查询数': len(dns_queries),
        'HTTP数据包数': len(http_packets),
        'HTTPS数据包数': len(https_packets),
        '阶段划分': {k: len(v) for k, v in stages.items()},
        '可能的登录包数': len(potential_login_packets)
    }
    
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    return {
        'packets': packets,
        'dns_queries': dns_queries,
        'http_packets': http_packets,
        'https_packets': https_packets,
        'stages': stages,
        'potential_login_packets': potential_login_packets
    }

if __name__ == '__main__':
    pcap_file = r'd:\桌面\计算机网络\课设1\程泽凯.pcapng'
    result = analyze_jwc_packets(pcap_file)
    
    print("\n" + "="*80)
    print("分析完成!")
    print("="*80)
