#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的教务处网站访问分析报告生成脚本
"""

from scapy.all import *
from scapy.layers.ppp import *
from scapy.layers.l2 import Ether
from collections import defaultdict, Counter
import struct

def analyze_complete(pcap_file):
    """完整分析pcapng文件"""
    
    print("正在读取数据包...")
    packets = rdpcap(pcap_file)
    total = len(packets)
    print(f"共读取 {total} 个数据包\n")
    
    # 分析结果存储
    results = {
        'total_packets': total,
        'dns_packets': [],
        'tcp_syn_packets': [],
        'tcp_synack_packets': [],
        'tcp_ack_packets': [],
        'tls_handshake_packets': [],
        'https_data_packets': [],
        'pppoe_session_packets': [],
        'stages': {
            'DNS解析阶段': [],
            'TCP三次握手阶段': [],
            'TLS握手阶段': [],
            'HTTPS数据传输阶段': []
        }
    }
    
    # 逐包分析
    for idx, pkt in enumerate(packets, 1):
        # PPPoE Session分析
        if Ether in pkt and pkt[Ether].type == 0x8864:
            results['pppoe_session_packets'].append(idx)
        
        # DNS分析
        if DNS in pkt:
            dns_info = {'num': idx}
            if UDP in pkt:
                dns_info['is_query'] = pkt[UDP].dport == 53
                dns_info['src_ip'] = pkt[IP].src if IP in pkt else 'N/A'
                dns_info['dst_ip'] = pkt[IP].dst if IP in pkt else 'N/A'
            
            if pkt[DNS].qd:
                try:
                    qname = pkt[DNS].qd.qname
                    dns_info['query'] = qname.decode() if isinstance(qname, bytes) else str(qname)
                except:
                    dns_info['query'] = 'Unknown'
            
            if pkt[DNS].an:
                dns_info['answers'] = []
                for i in range(pkt[DNS].ancount):
                    try:
                        if pkt[DNS].an[i].type == 1:  # A记录
                            dns_info['answers'].append(pkt[DNS].an[i].rdata)
                    except:
                        pass
            
            results['dns_packets'].append(dns_info)
            results['stages']['DNS解析阶段'].append(idx)
        
        # TCP分析
        if TCP in pkt:
            tcp_flags = pkt[TCP].flags
            
            # SYN包
            if tcp_flags == 'S':
                results['tcp_syn_packets'].append({
                    'num': idx,
                    'src_ip': pkt[IP].src,
                    'dst_ip': pkt[IP].dst,
                    'src_port': pkt[TCP].sport,
                    'dst_port': pkt[TCP].dport,
                    'seq': pkt[TCP].seq
                })
                results['stages']['TCP三次握手阶段'].append(idx)
            
            # SYN-ACK包
            elif tcp_flags == 'SA':
                results['tcp_synack_packets'].append({
                    'num': idx,
                    'src_ip': pkt[IP].src,
                    'dst_ip': pkt[IP].dst,
                    'src_port': pkt[TCP].sport,
                    'dst_port': pkt[TCP].dport,
                    'seq': pkt[TCP].seq,
                    'ack': pkt[TCP].ack
                })
                results['stages']['TCP三次握手阶段'].append(idx)
            
            # ACK包(可能是三次握手的第三步)
            elif tcp_flags == 'A' and len(pkt[TCP].payload) == 0:
                # 检查是否紧跟在SYN-ACK之后
                if results['tcp_synack_packets'] and idx - results['tcp_synack_packets'][-1]['num'] <= 5:
                    results['tcp_ack_packets'].append({
                        'num': idx,
                        'src_ip': pkt[IP].src,
                        'dst_ip': pkt[IP].dst,
                        'src_port': pkt[TCP].sport,
                        'dst_port': pkt[TCP].dport,
                        'ack': pkt[TCP].ack
                    })
                    results['stages']['TCP三次握手阶段'].append(idx)
            
            # HTTPS流量(端口443)
            if pkt[TCP].dport == 443 or pkt[TCP].sport == 443:
                if Raw in pkt:
                    payload = bytes(pkt[Raw].load)
                    # TLS握手(记录类型0x16)
                    if len(payload) > 0 and payload[0] == 0x16:
                        tls_info = {
                            'num': idx,
                            'src_ip': pkt[IP].src,
                            'dst_ip': pkt[IP].dst,
                            'src_port': pkt[TCP].sport,
                            'dst_port': pkt[TCP].dport,
                            'tls_type': 'Handshake'
                        }
                        
                        # 解析TLS握手类型
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
                            tls_info['handshake_type'] = tls_types.get(handshake_type, f'Unknown (0x{handshake_type:02x})')
                        
                        results['tls_handshake_packets'].append(tls_info)
                        results['stages']['TLS握手阶段'].append(idx)
                    # TLS应用数据(记录类型0x17)
                    elif len(payload) > 0 and payload[0] == 0x17:
                        results['https_data_packets'].append({
                            'num': idx,
                            'src_ip': pkt[IP].src,
                            'dst_ip': pkt[IP].dst,
                            'src_port': pkt[TCP].sport,
                            'dst_port': pkt[TCP].dport,
                            'data_len': len(payload)
                        })
                        results['stages']['HTTPS数据传输阶段'].append(idx)
    
    return results

def print_report(results):
    """打印完整报告"""
    
    print("="*100)
    print("教务处网站访问完整分析报告")
    print("="*100)
    
    # 一、基本信息
    print("\n【一、数据包捕获基本信息】")
    print(f"总数据包数: {results['total_packets']}")
    print(f"PPPoE Session数据包: {len(results['pppoe_session_packets'])}")
    print(f"DNS数据包: {len(results['dns_packets'])}")
    print(f"TCP SYN数据包: {len(results['tcp_syn_packets'])}")
    print(f"TCP SYN-ACK数据包: {len(results['tcp_synack_packets'])}")
    print(f"TLS握手数据包: {len(results['tls_handshake_packets'])}")
    print(f"HTTPS数据传输数据包: {len(results['https_data_packets'])}")
    
    # 二、阶段划分
    print("\n" + "="*100)
    print("【二、访问Web网站的阶段划分】")
    print("="*100)
    
    for stage_name, packet_nums in results['stages'].items():
        if packet_nums:
            print(f"\n{stage_name}:")
            print(f"  数据包数量: {len(packet_nums)}")
            print(f"  数据包序号: ", end="")
            
            # 分组显示序号
            if len(packet_nums) <= 50:
                print(packet_nums)
            else:
                print(packet_nums[:50])
                print(f"  ... (还有 {len(packet_nums)-50} 个)")
            
            # 显示该阶段完成的任务
            print(f"  完成任务: ", end="")
            if 'DNS' in stage_name:
                print("域名解析,将域名转换为IP地址")
            elif 'TCP三次握手' in stage_name:
                print("建立TCP连接,确保客户端和服务器之间的可靠连接")
            elif 'TLS握手' in stage_name:
                print("建立安全连接,协商加密算法,交换密钥,验证服务器身份")
            elif 'HTTPS数据传输' in stage_name:
                print("加密传输HTTP数据,包括请求和响应")
    
    # DNS详细信息
    if results['dns_packets']:
        print("\n" + "="*100)
        print("【DNS解析详细信息】")
        print("="*100)
        for dns in results['dns_packets']:
            print(f"\n数据包 #{dns['num']}:")
            print(f"  类型: {'DNS查询' if dns.get('is_query') else 'DNS响应'}")
            if 'src_ip' in dns:
                print(f"  源IP: {dns['src_ip']}")
                print(f"  目标IP: {dns['dst_ip']}")
            if 'query' in dns:
                print(f"  查询域名: {dns['query']}")
            if 'answers' in dns and dns['answers']:
                print(f"  解析结果: {', '.join(dns['answers'])}")
    
    # TCP三次握手详细信息
    print("\n" + "="*100)
    print("【TCP三次握手详细信息】")
    print("="*100)
    
    # 找出完整的三次握手序列
    handshakes = []
    for syn in results['tcp_syn_packets']:
        # 查找对应的SYN-ACK
        for synack in results['tcp_synack_packets']:
            if (synack['src_ip'] == syn['dst_ip'] and 
                synack['dst_ip'] == syn['src_ip'] and
                synack['src_port'] == syn['dst_port'] and
                synack['dst_port'] == syn['src_port'] and
                synack['num'] > syn['num'] and
                synack['num'] - syn['num'] < 10):
                
                # 查找对应的ACK
                for ack in results['tcp_ack_packets']:
                    if (ack['src_ip'] == syn['src_ip'] and
                        ack['dst_ip'] == syn['dst_ip'] and
                        ack['src_port'] == syn['src_port'] and
                        ack['dst_port'] == syn['dst_port'] and
                        ack['num'] > synack['num'] and
                        ack['num'] - synack['num'] < 10):
                        
                        handshakes.append({
                            'syn': syn,
                            'synack': synack,
                            'ack': ack
                        })
                        break
                break
    
    print(f"\n找到 {len(handshakes)} 个完整的TCP三次握手序列")
    for i, hs in enumerate(handshakes[:5], 1):  # 显示前5个
        print(f"\n三次握手序列 {i}:")
        print(f"  1. SYN包 (#{hs['syn']['num']}): {hs['syn']['src_ip']}:{hs['syn']['src_port']} -> {hs['syn']['dst_ip']}:{hs['syn']['dst_port']}")
        print(f"     Seq={hs['syn']['seq']}")
        print(f"  2. SYN-ACK包 (#{hs['synack']['num']}): {hs['synack']['src_ip']}:{hs['synack']['src_port']} -> {hs['synack']['dst_ip']}:{hs['synack']['dst_port']}")
        print(f"     Seq={hs['synack']['seq']}, Ack={hs['synack']['ack']}")
        print(f"  3. ACK包 (#{hs['ack']['num']}): {hs['ack']['src_ip']}:{hs['ack']['src_port']} -> {hs['ack']['dst_ip']}:{hs['ack']['dst_port']}")
        print(f"     Ack={hs['ack']['ack']}")
    
    # TLS握手详细信息
    if results['tls_handshake_packets']:
        print("\n" + "="*100)
        print("【TLS握手详细信息】")
        print("="*100)
        for tls in results['tls_handshake_packets'][:10]:  # 显示前10个
            print(f"\n数据包 #{tls['num']}:")
            print(f"  {tls['src_ip']}:{tls['src_port']} -> {tls['dst_ip']}:{tls['dst_port']}")
            print(f"  TLS握手类型: {tls.get('handshake_type', 'Unknown')}")
    
    # 三、登录信息分析
    print("\n" + "="*100)
    print("【三、登录信息分析】")
    print("="*100)
    print("\n分析结果:")
    print("  ✗ 无法从数据包中分析到明文的用户名和密码")
    print("\n原因:")
    print("  1. 教务处网站使用HTTPS协议(端口443)进行通信")
    print("  2. 所有HTTP数据(包括用户名和密码)都经过TLS/SSL加密")
    print("  3. 加密后的数据在网络传输中表现为随机字节流,无法直接读取")
    print("\n技术说明:")
    print("  - TLS记录类型0x17表示应用数据(Application Data)")
    print("  - 这些数据包含加密的HTTP请求和响应")
    print("  - 即使捕获到包含登录信息的数据包,也无法解密查看")
    print("  - 这正是HTTPS协议设计的安全目标:保护用户隐私和数据安全")
    
    print(f"\nHTTPS加密数据包统计:")
    print(f"  - TLS握手包: {len(results['tls_handshake_packets'])} 个")
    print(f"  - 加密数据包: {len(results['https_data_packets'])} 个")
    
    return handshakes

def analyze_pppoe_headers(pcap_file):
    """分析PPPoE协议头部"""
    
    print("\n" + "="*100)
    print("【PPPoE协议头部分析】")
    print("="*100)
    
    packets = rdpcap(pcap_file)
    
    pppoe_packets = []
    for idx, pkt in enumerate(packets, 1):
        if Ether in pkt and pkt[Ether].type == 0x8864:
            pppoe_packets.append((idx, pkt))
    
    if not pppoe_packets:
        print("\n⚠ 未找到PPPoE Session数据包")
        return
    
    print(f"\n找到 {len(pppoe_packets)} 个PPPoE Session数据包")
    print("\n典型PPPoE Session数据包头部分析:")
    
    # 分析前3个PPPoE包
    for i, (num, pkt) in enumerate(pppoe_packets[:3], 1):
        print(f"\n{'='*80}")
        print(f"示例 {i}: 数据包 #{num}")
        print(f"{'='*80}")
        
        # 以太网层
        if Ether in pkt:
            print("\n【以太网帧头部 (Ethernet II)】")
            print(f"  目标MAC地址 (Destination): {pkt[Ether].dst}")
            print(f"    说明: 数据包的目标设备MAC地址")
            print(f"  源MAC地址 (Source): {pkt[Ether].src}")
            print(f"    说明: 数据包的源设备MAC地址")
            print(f"  类型 (Type): 0x{pkt[Ether].type:04x}")
            print(f"    说明: 0x8864表示PPPoE Session阶段数据包")
        
        # PPPoE层
        raw_bytes = bytes(pkt)
        eth_header_len = 14  # 以太网头部14字节
        
        if len(raw_bytes) > eth_header_len + 6:
            pppoe_header = raw_bytes[eth_header_len:eth_header_len+6]
            
            version_type = pppoe_header[0]
            version = (version_type >> 4) & 0x0F
            type_val = version_type & 0x0F
            code = pppoe_header[1]
            session_id = struct.unpack('!H', pppoe_header[2:4])[0]
            length = struct.unpack('!H', pppoe_header[4:6])[0]
            
            print("\n【PPPoE头部】")
            print(f"  版本 (Version): {version}")
            print(f"    说明: PPPoE协议版本号,固定为1")
            print(f"  类型 (Type): {type_val}")
            print(f"    说明: PPPoE类型,固定为1")
            print(f"  代码 (Code): 0x{code:02x}")
            print(f"    说明: 0x00表示Session Data(会话数据)")
            print(f"  会话ID (Session ID): 0x{session_id:04x} (十进制: {session_id})")
            print(f"    说明: 唯一标识此PPPoE会话的ID,由服务器在连接建立时分配")
            print(f"  长度 (Length): {length} 字节")
            print(f"    说明: PPP负载的长度(不包括PPPoE头部)")
            
            # PPP协议
            if len(raw_bytes) > eth_header_len + 8:
                ppp_protocol = struct.unpack('!H', raw_bytes[eth_header_len+6:eth_header_len+8])[0]
                print("\n【PPP协议字段】")
                print(f"  协议 (Protocol): 0x{ppp_protocol:04x}")
                ppp_protocols = {
                    0x0021: "IPv4 - 互联网协议版本4",
                    0x0057: "IPv6 - 互联网协议版本6",
                    0xc021: "LCP - 链路控制协议",
                    0x8021: "IPCP - IP控制协议",
                    0xc023: "PAP - 密码认证协议",
                    0xc223: "CHAP - 质询握手认证协议"
                }
                print(f"    说明: {ppp_protocols.get(ppp_protocol, '未知协议')}")
        
        # IP层
        if IP in pkt:
            print("\n【IP头部】")
            print(f"  源IP地址 (Source IP): {pkt[IP].src}")
            print(f"  目标IP地址 (Destination IP): {pkt[IP].dst}")
            print(f"  协议 (Protocol): {pkt[IP].proto}")
            proto_names = {1: "ICMP", 6: "TCP", 17: "UDP"}
            print(f"    说明: {proto_names.get(pkt[IP].proto, '其他协议')}")
            print(f"  TTL (Time To Live): {pkt[IP].ttl}")
            print(f"    说明: 数据包的生存时间,每经过一个路由器减1")
        
        # TCP层
        if TCP in pkt:
            print("\n【TCP头部】")
            print(f"  源端口 (Source Port): {pkt[TCP].sport}")
            print(f"  目标端口 (Destination Port): {pkt[TCP].dport}")
            if pkt[TCP].dport == 443 or pkt[TCP].sport == 443:
                print(f"    说明: 端口443用于HTTPS加密通信")
            print(f"  序列号 (Sequence Number): {pkt[TCP].seq}")
            print(f"  确认号 (Acknowledgment Number): {pkt[TCP].ack}")
            print(f"  标志位 (Flags): {pkt[TCP].flags}")
            flag_meanings = {
                'S': 'SYN-同步',
                'A': 'ACK-确认',
                'F': 'FIN-结束',
                'P': 'PSH-推送',
                'R': 'RST-重置'
            }
            flags_str = ', '.join([f"{flag}({flag_meanings.get(str(flag), '未知')})" 
                                  for flag in str(pkt[TCP].flags)])
            print(f"    说明: {flags_str}")

if __name__ == '__main__':
    pcap_file = r'd:\桌面\计算机网络\课设1\程泽凯.pcapng'
    
    # 完整分析
    results = analyze_complete(pcap_file)
    
    # 打印报告
    handshakes = print_report(results)
    
    # PPPoE头部分析
    analyze_pppoe_headers(pcap_file)
    
    print("\n" + "="*100)
    print("分析完成!")
    print("="*100)
