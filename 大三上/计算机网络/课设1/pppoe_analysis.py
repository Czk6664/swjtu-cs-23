#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPPoE 数据包完整分析脚本
分析访问教务处网站的完整过程
"""

import sys
from collections import Counter, defaultdict

try:
    from scapy.all import rdpcap, Ether, IP, TCP, UDP, ICMP, DNS, Raw
    from scapy.layers.ppp import PPPoE, PPPoED
    from scapy.layers.http import HTTPRequest, HTTPResponse
except ImportError as e:
    print(f"错误: 需要安装 scapy 库 - {e}")
    print("请运行: pip install scapy")
    sys.exit(1)

def analyze_pppoe_stages(packets):
    """分析 PPPoE 各个阶段"""
    print("\n" + "=" * 80)
    print("二、分析访问过程的各个阶段")
    print("=" * 80)
    
    stages = {
        'PPPoE Discovery': [],
        'PPP LCP': [],
        'PPP Authentication': [],
        'PPP IPCP': [],
        'DNS Query': [],
        'TCP Connection': [],
        'HTTP Request': [],
        'HTTP Response': [],
        'Data Transfer': []
    }
    
    for i, pkt in enumerate(packets):
        pkt_num = i + 1
        
        # PPPoE Discovery 阶段
        if PPPoED in pkt:
            code = pkt[PPPoED].code
            code_names = {
                0x09: 'PADI',
                0x07: 'PADO', 
                0x19: 'PADR',
                0x65: 'PADS',
                0xa7: 'PADT'
            }
            stages['PPPoE Discovery'].append((pkt_num, code_names.get(code, f'Unknown-{code}')))
        
        # DNS 查询
        if DNS in pkt:
            if pkt[DNS].qr == 0:  # Query
                stages['DNS Query'].append((pkt_num, 'DNS Query'))
            else:  # Response
                stages['DNS Query'].append((pkt_num, 'DNS Response'))
        
        # TCP 连接建立
        if TCP in pkt:
            flags = pkt[TCP].flags
            if flags & 0x02:  # SYN
                if flags & 0x10:  # SYN-ACK
                    stages['TCP Connection'].append((pkt_num, 'SYN-ACK'))
                else:
                    stages['TCP Connection'].append((pkt_num, 'SYN'))
            elif flags & 0x01 and not (flags & 0x10):  # FIN without ACK
                stages['TCP Connection'].append((pkt_num, 'FIN'))
        
        # HTTP 请求和响应
        if Raw in pkt and TCP in pkt:
            payload = bytes(pkt[Raw].load)
            if payload.startswith(b'GET ') or payload.startswith(b'POST '):
                stages['HTTP Request'].append((pkt_num, 'HTTP Request'))
            elif payload.startswith(b'HTTP/'):
                stages['HTTP Response'].append((pkt_num, 'HTTP Response'))
    
    # 打印各阶段分析
    print("\n1. 访问Web网站的过程分为以下阶段:\n")
    
    stage_descriptions = {
        'PPPoE Discovery': 'PPPoE发现阶段 - 建立PPPoE连接',
        'DNS Query': 'DNS解析阶段 - 解析域名jwc.swjtu.edu.cn的IP地址',
        'TCP Connection': 'TCP连接建立阶段 - 三次握手建立TCP连接',
        'HTTP Request': 'HTTP请求阶段 - 发送HTTP请求获取网页',
        'HTTP Response': 'HTTP响应阶段 - 接收服务器响应',
    }
    
    for stage_name, description in stage_descriptions.items():
        if stages[stage_name]:
            print(f"【{stage_name}】")
            print(f"  任务: {description}")
            print(f"  相关报文序号: {[num for num, _ in stages[stage_name][:20]]}")
            if len(stages[stage_name]) > 20:
                print(f"  (还有 {len(stages[stage_name]) - 20} 个相关报文...)")
            print()
    
    return stages

def analyze_pppoe_headers(packets):
    """分析 PPPoE 各阶段的数据包头部"""
    print("\n" + "=" * 80)
    print("2. PPPoE各阶段典型数据包头部字段分析")
    print("=" * 80)
    
    pppoe_discovery_found = False
    pppoe_session_found = False
    
    for i, pkt in enumerate(packets):
        # 分析 PPPoE Discovery 包
        if PPPoED in pkt and not pppoe_discovery_found:
            pppoe_discovery_found = True
            print(f"\n【PPPoE Discovery 阶段 - 包 #{i+1}】")
            print("-" * 80)
            
            if Ether in pkt:
                print("以太网帧头部:")
                print(f"  目的MAC地址 (Destination): {pkt[Ether].dst}")
                print(f"    含义: 目标设备的物理地址")
                print(f"  源MAC地址 (Source): {pkt[Ether].src}")
                print(f"    含义: 发送设备的物理地址")
                print(f"  类型 (Type): 0x{pkt[Ether].type:04x}")
                print(f"    含义: 上层协议类型 (0x8863=PPPoE Discovery, 0x8864=PPPoE Session)")
            
            print("\nPPPoE Discovery 头部:")
            print(f"  版本 (Version): {(pkt[PPPoED].version >> 4) & 0x0F}")
            print(f"    含义: PPPoE协议版本号")
            print(f"  类型 (Type): {pkt[PPPoED].version & 0x0F}")
            print(f"    含义: PPPoE报文类型")
            print(f"  代码 (Code): 0x{pkt[PPPoED].code:02x}")
            code_meanings = {
                0x09: 'PADI - 客户端发起连接请求',
                0x07: 'PADO - 服务器响应连接请求',
                0x19: 'PADR - 客户端请求建立会话',
                0x65: 'PADS - 服务器确认会话建立',
                0xa7: 'PADT - 终止会话'
            }
            print(f"    含义: {code_meanings.get(pkt[PPPoED].code, '未知代码')}")
            print(f"  会话ID (Session ID): 0x{pkt[PPPoED].sessionid:04x}")
            print(f"    含义: PPPoE会话标识符 (Discovery阶段通常为0x0000)")
            print(f"  长度 (Length): {pkt[PPPoED].len}")
            print(f"    含义: 负载数据长度(字节)")
        
        # 分析 PPPoE Session 包
        if PPPoE in pkt and not pppoe_session_found:
            pppoe_session_found = True
            print(f"\n【PPPoE Session 阶段 - 包 #{i+1}】")
            print("-" * 80)
            
            if Ether in pkt:
                print("以太网帧头部:")
                print(f"  目的MAC地址: {pkt[Ether].dst}")
                print(f"  源MAC地址: {pkt[Ether].src}")
                print(f"  类型: 0x{pkt[Ether].type:04x} (PPPoE Session)")
            
            print("\nPPPoE Session 头部:")
            print(f"  版本 (Version): {(pkt[PPPoE].version >> 4) & 0x0F}")
            print(f"    含义: PPPoE协议版本号")
            print(f"  类型 (Type): {pkt[PPPoE].version & 0x0F}")
            print(f"    含义: PPPoE报文类型")
            print(f"  代码 (Code): 0x{pkt[PPPoE].code:02x}")
            print(f"    含义: Session阶段代码为0x00")
            print(f"  会话ID (Session ID): 0x{pkt[PPPoE].sessionid:04x}")
            print(f"    含义: 唯一标识此PPPoE会话")
            print(f"  长度 (Length): {pkt[PPPoE].len}")
            print(f"    含义: PPP负载长度")
            
            if IP in pkt:
                print("\nIP头部 (封装在PPPoE中):")
                print(f"  源IP地址: {pkt[IP].src}")
                print(f"  目的IP地址: {pkt[IP].dst}")
                print(f"  协议: {pkt[IP].proto} ({pkt[IP].proto}=TCP, 17=UDP, 1=ICMP)")
        
        if pppoe_discovery_found and pppoe_session_found:
            break

def find_credentials(packets):
    """查找登录凭证信息"""
    print("\n" + "=" * 80)
    print("三、登录凭证分析")
    print("=" * 80)
    
    credentials_found = []
    
    for i, pkt in enumerate(packets):
        if Raw in pkt and TCP in pkt:
            try:
                payload = bytes(pkt[Raw].load)
                payload_str = payload.decode('utf-8', errors='ignore').lower()
                
                # 查找可能包含用户名密码的关键字
                keywords = ['username', 'password', 'user', 'pass', 'login', 'account', 
                           'userid', 'passwd', 'pwd', 'name=', 'pwd=']
                
                if any(keyword in payload_str for keyword in keywords):
                    credentials_found.append({
                        'packet_num': i + 1,
                        'src': pkt[IP].src if IP in pkt else 'N/A',
                        'dst': pkt[IP].dst if IP in pkt else 'N/A',
                        'sport': pkt[TCP].sport if TCP in pkt else 'N/A',
                        'dport': pkt[TCP].dport if TCP in pkt else 'N/A',
                        'payload': payload,
                        'payload_str': payload_str
                    })
            except:
                pass
    
    if credentials_found:
        print(f"\n发现 {len(credentials_found)} 个可能包含登录信息的数据包:\n")
        
        for cred in credentials_found[:5]:  # 只显示前5个
            print(f"【数据包 #{cred['packet_num']}】")
            print(f"  源地址: {cred['src']}:{cred['sport']}")
            print(f"  目的地址: {cred['dst']}:{cred['dport']}")
            print(f"  负载长度: {len(cred['payload'])} 字节")
            
            # 显示十六进制和ASCII
            print("\n  十六进制内容 (前256字节):")
            hex_data = cred['payload'][:256]
            for j in range(0, len(hex_data), 16):
                hex_part = ' '.join(f'{b:02x}' for b in hex_data[j:j+16])
                ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in hex_data[j:j+16])
                print(f"    {j:04x}: {hex_part:<48} {ascii_part}")
            
            print("\n  可读文本内容 (部分):")
            readable = cred['payload_str'][:500]
            print(f"    {readable}")
            print("\n" + "-" * 80)
    else:
        print("\n未在明文中发现用户名和密码信息。")
        print("可能原因:")
        print("  1. 使用了HTTPS加密传输")
        print("  2. 登录信息经过编码或加密")
        print("  3. 需要进一步分析POST请求的数据包")

def main():
    filename = "ppoe.pcapng"
    
    print("=" * 80)
    print("PPPoE 数据包分析报告")
    print("分析文件: " + filename)
    print("=" * 80)
    
    try:
        packets = rdpcap(filename)
        print(f"\n总数据包数量: {len(packets)}")
    except Exception as e:
        print(f"读取文件失败: {e}")
        return
    
    # 基本统计
    print("\n" + "=" * 80)
    print("一、数据包基本统计")
    print("=" * 80)
    
    protocol_count = Counter()
    mac_addresses = set()
    ip_addresses = set()
    
    for pkt in packets:
        if Ether in pkt:
            mac_addresses.add(pkt[Ether].src)
            mac_addresses.add(pkt[Ether].dst)
        
        if IP in pkt:
            ip_addresses.add(pkt[IP].src)
            ip_addresses.add(pkt[IP].dst)
            
            if TCP in pkt:
                protocol_count['TCP'] += 1
            elif UDP in pkt:
                protocol_count['UDP'] += 1
            elif ICMP in pkt:
                protocol_count['ICMP'] += 1
        
        if PPPoED in pkt:
            protocol_count['PPPoE Discovery'] += 1
        elif PPPoE in pkt:
            protocol_count['PPPoE Session'] += 1
        
        if DNS in pkt:
            protocol_count['DNS'] += 1
    
    print(f"\nMAC地址数量: {len(mac_addresses)}")
    for mac in sorted(mac_addresses):
        print(f"  {mac}")
    
    print(f"\nIP地址数量: {len(ip_addresses)}")
    for ip in sorted(ip_addresses):
        print(f"  {ip}")
    
    print("\n协议分布:")
    for proto, count in sorted(protocol_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {proto}: {count} 个数据包")
    
    # 分析各阶段
    stages = analyze_pppoe_stages(packets)
    
    # 分析PPPoE头部
    analyze_pppoe_headers(packets)
    
    # 查找登录凭证
    find_credentials(packets)
    
    print("\n" + "=" * 80)
    print("分析完成!")
    print("=" * 80)

if __name__ == "__main__":
    main()
