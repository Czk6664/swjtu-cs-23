PPPoE数据包头部字段分析报告

分析文件: 2023112621.pcapng
分析时间: 2025年11月25日
本机IP: 10.169.227.162
本机MAC: b0:25:aa:5b:26:c4
PPPoE Session ID: 0x8cfb

---

一、抓包文件中的PPPoE阶段说明

本次抓包文件只包含PPPoE会话阶段(Session Stage)的数据包,不包含发现阶段(Discovery Stage)。

已捕获的阶段:
- PPPoE Session阶段 (以太网类型: 0x8864)
- 所有数据包的Session ID均为: 0x8cfb

未捕获的阶段:
- PPPoE Discovery阶段 (以太网类型: 0x8863)
- LCP协商阶段 (PPP协议: 0xc021)
- PAP/CHAP认证阶段 (PPP协议: 0xc023/0xc223)
- IPCP协商阶段 (PPP协议: 0x8021)

原因: 抓包时PPPoE连接已经建立完成

---

二、PPPoE会话阶段数据包头部字段详细分析

典型数据包: 数据包 1

基本信息:
- 帧序号: 1
- 帧长度: 62 bytes
- 捕获时间: 2025-11-24 18:13:04.942498
- 协议栈: Ethernet → PPPoE Session → PPP → IPv4 → TCP

完整帧结构:

┌─────────────────────────────────────────────────────────────┐
│                    以太网帧头部 (14字节)                      │
├─────────────────────────────────────────────────────────────┤
│ 目标MAC地址: 00:00:5e:00:01:01 (PPPoE网关)                   │
│ 源MAC地址:   b0:25:aa:5b:26:c4 (本机网卡)                    │
│ 类型:        0x8864 (PPPoE Session)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    PPPoE头部 (6字节)                         │
├─────────────────────────────────────────────────────────────┤
│ Version:     1 (0001)                                        │
│ Type:        1 (0001)                                        │
│ Code:        0x00 (Session Data)                             │
│ Session ID:  0x8cfb                                          │
│ Length:      42                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    PPP头部 (2字节)                           │
├─────────────────────────────────────────────────────────────┤
│ Protocol:    0x0021 (IPv4)                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    IP头部 (20字节)                           │
├─────────────────────────────────────────────────────────────┤
│ 源IP:        10.169.227.162                                  │
│ 目标IP:      101.91.29.17                                    │
│ 协议:        TCP (6)                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    TCP头部 (20字节)                          │
├─────────────────────────────────────────────────────────────┤
│ 源端口:      63067                                           │
│ 目标端口:    443                                             │
│ 标志:        ACK                                             │
└─────────────────────────────────────────────────────────────┘

---

三、各层头部字段详细解析

1. 以太网帧头部 (Ethernet II Header)

字段结构:

| 偏移 | 字段名称 | 长度 | 十六进制值 | 含义 |
|------|---------|------|-----------|------|
| 0-5  | 目标MAC地址 | 6字节 | 00:00:5e:00:01:01 | PPPoE网关的MAC地址 |
| 6-11 | 源MAC地址 | 6字节 | b0:25:aa:5b:26:c4 | 本机网卡的MAC地址 |
| 12-13 | 类型 | 2字节 | 0x8864 | PPPoE Session帧 |

字段详解:

目标MAC地址 (Destination MAC Address)
- 值: 00:00:5e:00:01:01
- 含义: 数据包要发送到的设备MAC地址
- 说明: PPPoE网关(AC访问集中器)的MAC地址
- 特点: 00:00:5e是IANA分配给VRRP的OUI

源MAC地址 (Source MAC Address)
- 值: b0:25:aa:5b:26:c4
- 含义: 发送数据包的设备MAC地址
- 说明: 本机网卡的物理地址
- 厂商: AIstone Global

类型 (EtherType)
- 值: 0x8864
- 含义: 指示以太网帧中封装的上层协议类型
- 说明: 0x8864表示PPPoE Session(会话阶段)
- 对比: 0x8863表示PPPoE Discovery(发现阶段)

---

2. PPPoE头部 (PPPoE Header)

字段结构:

| 偏移 | 字段名称 | 长度 | 十六进制值 | 含义 |
|------|---------|------|-----------|------|
| 14   | Version + Type | 1字节 | 0x11 | 版本号(1)和类型(1) |
| 15   | Code | 1字节 | 0x00 | 会话数据包代码 |
| 16-17 | Session ID | 2字节 | 0x8cfb | 会话标识符 |
| 18-19 | Length | 2字节 | 0x002a (42) | PPP载荷长度 |

字段详解:

Version (版本)
- 位置: 第14字节的高4位
- 值: 1 (0001)
- 含义: PPPoE协议版本号
- 说明: 当前PPPoE协议版本固定为1

Type (类型)
- 位置: 第14字节的低4位
- 值: 1 (0001)
- 含义: PPPoE帧类型
- 说明: 固定为1,表示标准PPPoE帧

Code (代码)
- 位置: 第15字节
- 值: 0x00
- 含义: PPPoE数据包的类型代码
- 说明: 0x00表示Session Data(会话数据)

Code字段所有可能的取值:
- 0x00: Session Data (会话数据) - 本次抓包中的值
- 0x07: PADO (PPPoE Active Discovery Offer)
- 0x09: PADI (PPPoE Active Discovery Initiation)
- 0x19: PADR (PPPoE Active Discovery Request)
- 0x65: PADS (PPPoE Active Discovery Session-confirmation)
- 0xa7: PADT (PPPoE Active Discovery Terminate)

Session ID (会话标识符)
- 位置: 第16-17字节
- 值: 0x8cfb (十进制: 36090)
- 含义: 唯一标识本次PPPoE会话
- 说明: 由AC在PADS阶段分配,会话期间保持不变
- 作用: 区分同一物理链路上的多个PPPoE会话

Length (长度)
- 位置: 第18-19字节
- 值: 0x002a (十进制: 42)
- 含义: PPP载荷的长度(字节数)
- 说明: 不包括PPPoE头部本身的6字节
- 计算: PPP头部(2) + IP头部(20) + TCP头部(20) = 42字节

---

3. PPP头部 (PPP Header)

字段结构:

| 偏移 | 字段名称 | 长度 | 十六进制值 | 含义 |
|------|---------|------|-----------|------|
| 20-21 | Protocol | 2字节 | 0x0021 | 封装的上层协议类型 |

字段详解:

Protocol (协议)
- 位置: 第20-21字节
- 值: 0x0021
- 含义: 指示PPP帧中封装的网络层协议
- 说明: 0x0021表示IPv4协议

PPP Protocol字段常见取值:

数据协议:
- 0x0021: IPv4 - 本次抓包中的值
- 0x0057: IPv6
- 0x002b: IPX
- 0x003d: Multi-Link

控制协议:
- 0xc021: LCP (Link Control Protocol)
- 0x8021: IPCP (IP Control Protocol)
- 0x8057: IPv6CP
- 0xc023: PAP (Password Authentication Protocol)
- 0xc223: CHAP (Challenge Handshake Authentication Protocol)

---

4. 完整数据包十六进制分析

数据包 1 的完整十六进制内容:

偏移量    十六进制数据                                      ASCII
0000      00 00 5e 00 01 01 b0 25 aa 5b 26 c4 88 64 11 00   ..^....%.[&..d..
          │           │           │           │     │  │
          └─目标MAC    └─源MAC      └─类型     │     │  └─PPPoE Code
                                    (0x8864)   │     └─Ver+Type
                                               └─Session ID高字节

0010      8c fb 00 2a 00 21 45 00 00 28 4b 27 40 00 80 06   ...*.!E..(K'@...
          │     │     │     │
          │     │     │     └─IP头部开始 (0x45 = IPv4)
          │     │     └─PPP Protocol (0x0021 = IPv4)
          │     └─PPPoE Length (0x002a = 42字节)
          └─Session ID低字节 (0x8cfb)

0020      3e f1 0a a9 e3 a2 65 5b 1d 11 f6 5b 01 bb 9f 14   >.....e[...[....
                │           │           │     │
                └─源IP       └─目标IP     └─源端口 └─目标端口
              (10.169.227.162) (101.91.29.17) (63067) (443)

0030      01 5e ca ed 2c 77 50 10 00 ff ae 2f 00 00         .^..,wP..../.
                            │     │
                            └─TCP Flags (0x10 = ACK)
                                  └─窗口大小

---

四、PPPoE其他阶段典型数据包头部字段分析(理论)

虽然本次抓包未捕获PPPoE建立过程,但以下是各阶段典型数据包的头部字段分析:

阶段1: PADI数据包 (PPPoE Active Discovery Initiation)

功能: 客户端广播寻找可用的AC(访问集中器)

以太网帧头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| 目标MAC地址 | 6字节 | FF:FF:FF:FF:FF:FF | 广播地址,寻找所有AC |
| 源MAC地址 | 6字节 | 客户端MAC | 发送方MAC地址 |
| 类型 | 2字节 | 0x8863 | PPPoE Discovery |

PPPoE头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Version | 4位 | 1 | PPPoE版本 |
| Type | 4位 | 1 | PPPoE类型 |
| Code | 1字节 | 0x09 | PADI代码 |
| Session ID | 2字节 | 0x0000 | 发现阶段固定为0 |
| Length | 2字节 | Tag总长度 | 载荷长度 |

Tag字段:
- Service-Name Tag (0x0101): 请求的服务名称
- Host-Uniq Tag (0x0103): 主机唯一标识符

十六进制示例:
```
0000  ff ff ff ff ff ff b0 25 aa 5b 26 c4 88 63 11 09
      │                 │                 │     │  │
      └─广播MAC          └─源MAC           │     │  └─Code(PADI)
                                          │     └─Ver+Type
                                          └─类型(0x8863)

0010  00 00 00 0c 01 01 00 00 01 03 00 04 xx xx xx xx
      │     │     │           │
      │     │     └─Service-Name Tag
      │     └─Length
      └─Session ID(0x0000)
```

---

阶段2: PADO数据包 (PPPoE Active Discovery Offer)

功能: AC响应客户端,提供服务

以太网帧头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| 目标MAC地址 | 6字节 | 客户端MAC | 单播回复客户端 |
| 源MAC地址 | 6字节 | AC的MAC | AC的MAC地址 |
| 类型 | 2字节 | 0x8863 | PPPoE Discovery |

PPPoE头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Version | 4位 | 1 | PPPoE版本 |
| Type | 4位 | 1 | PPPoE类型 |
| Code | 1字节 | 0x07 | PADO代码 |
| Session ID | 2字节 | 0x0000 | 发现阶段固定为0 |
| Length | 2字节 | Tag总长度 | 载荷长度 |

Tag字段:
- AC-Name Tag (0x0102): AC的名称
- Service-Name Tag (0x0101): 提供的服务
- AC-Cookie Tag (0x0104): AC的Cookie

十六进制示例:
```
0000  b0 25 aa 5b 26 c4 28 6e d4 63 55 53 88 63 11 07
      │                 │                 │     │  │
      └─客户端MAC        └─AC MAC          │     │  └─Code(PADO)
                                          │     └─Ver+Type
                                          └─类型(0x8863)

0010  00 00 00 20 01 02 00 08 48 75 61 77 65 69 41 43
      │     │     │           │
      │     │     └─AC-Name Tag
      │     └─Length
      └─Session ID(0x0000)
                            "HuaweiAC"
```

---

阶段3: PADR数据包 (PPPoE Active Discovery Request)

功能: 客户端选择AC并请求建立会话

以太网帧头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| 目标MAC地址 | 6字节 | 选中的AC MAC | 单播到选中的AC |
| 源MAC地址 | 6字节 | 客户端MAC | 客户端MAC地址 |
| 类型 | 2字节 | 0x8863 | PPPoE Discovery |

PPPoE头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Version | 4位 | 1 | PPPoE版本 |
| Type | 4位 | 1 | PPPoE类型 |
| Code | 1字节 | 0x19 | PADR代码 |
| Session ID | 2字节 | 0x0000 | 发现阶段固定为0 |
| Length | 2字节 | Tag总长度 | 载荷长度 |

Tag字段:
- Service-Name Tag (0x0101): 请求的服务
- AC-Cookie Tag (0x0104): 从PADO获得的Cookie

十六进制示例:
```
0000  28 6e d4 63 55 53 b0 25 aa 5b 26 c4 88 63 11 19
      │                 │                 │     │  │
      └─AC MAC          └─客户端MAC        │     │  └─Code(PADR)
                                          │     └─Ver+Type
                                          └─类型(0x8863)

0010  00 00 00 18 01 01 00 00 01 04 00 10 xx xx xx xx
      │     │     │           │
      │     │     └─Service-Name Tag
      │     └─Length
      └─Session ID(0x0000)
                            └─AC-Cookie
```

---

阶段4: PADS数据包 (PPPoE Active Discovery Session-confirmation)

功能: AC确认会话建立并分配Session ID

以太网帧头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| 目标MAC地址 | 6字节 | 客户端MAC | 单播到客户端 |
| 源MAC地址 | 6字节 | AC的MAC | AC的MAC地址 |
| 类型 | 2字节 | 0x8863 | PPPoE Discovery |

PPPoE头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Version | 4位 | 1 | PPPoE版本 |
| Type | 4位 | 1 | PPPoE类型 |
| Code | 1字节 | 0x65 | PADS代码 |
| Session ID | 2字节 | 0x8cfb | 分配的会话ID |
| Length | 2字节 | Tag总长度 | 载荷长度 |

Tag字段:
- Service-Name Tag (0x0101): 确认的服务

十六进制示例:
```
0000  b0 25 aa 5b 26 c4 28 6e d4 63 55 53 88 63 11 65
      │                 │                 │     │  │
      └─客户端MAC        └─AC MAC          │     │  └─Code(PADS)
                                          │     └─Ver+Type
                                          └─类型(0x8863)

0010  8c fb 00 0c 01 01 00 00
      │     │     │
      │     │     └─Service-Name Tag
      │     └─Length
      └─Session ID(0x8cfb) ← 重要!分配的会话ID
```

关键点: 从此刻起,Session ID从0x0000变为0x8cfb,后续所有数据包都使用这个ID

---

阶段5: LCP Configure-Request数据包

功能: 协商链路控制参数

以太网帧头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| 目标MAC地址 | 6字节 | 对方MAC | 对方MAC地址 |
| 源MAC地址 | 6字节 | 本机MAC | 本机MAC地址 |
| 类型 | 2字节 | 0x8864 | PPPoE Session |

PPPoE头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Version | 4位 | 1 | PPPoE版本 |
| Type | 4位 | 1 | PPPoE类型 |
| Code | 1字节 | 0x00 | Session Data |
| Session ID | 2字节 | 0x8cfb | 已分配的会话ID |
| Length | 2字节 | PPP载荷长度 | 载荷长度 |

PPP头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Protocol | 2字节 | 0xc021 | LCP协议 |

LCP头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Code | 1字节 | 0x01 | Configure-Request |
| Identifier | 1字节 | 0x01 | 请求标识符 |
| Length | 2字节 | LCP包长度 | 包括头部和选项 |

LCP Options:
- MRU (0x01): 最大接收单元,通常1492
- Auth-Protocol (0x03): 认证协议(PAP/CHAP)
- Magic-Number (0x05): 魔术字,检测环路
- Protocol-Field-Compression (0x07): 协议字段压缩
- AC-Field-Compression (0x08): 地址控制字段压缩

十六进制示例:
```
0000  28 6e d4 63 55 53 b0 25 aa 5b 26 c4 88 64 11 00
      │                 │                 │     │  │
      └─对方MAC          └─本机MAC         │     │  └─Code(Session)
                                          │     └─Ver+Type
                                          └─类型(0x8864)

0010  8c fb 00 18 c0 21 01 01 00 16 01 04 05 d4 03 04
      │     │     │     │  │  │     │     │
      │     │     │     │  │  │     │     └─Auth-Protocol
      │     │     │     │  │  │     └─MRU Option
      │     │     │     │  │  └─Length
      │     │     │     │  └─Identifier
      │     │     │     └─Code(Configure-Request)
      │     │     └─Protocol(LCP)
      │     └─Length
      └─Session ID(0x8cfb)

0020  c0 23 05 06 xx xx xx xx
      │     │
      │     └─Magic-Number Option
      └─PAP(0xc023)
```

---

阶段6: PAP Authenticate-Request数据包

功能: 发送用户名和密码进行认证

以太网帧头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| 目标MAC地址 | 6字节 | AC的MAC | AC的MAC地址 |
| 源MAC地址 | 6字节 | 客户端MAC | 客户端MAC地址 |
| 类型 | 2字节 | 0x8864 | PPPoE Session |

PPPoE头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Version | 4位 | 1 | PPPoE版本 |
| Type | 4位 | 1 | PPPoE类型 |
| Code | 1字节 | 0x00 | Session Data |
| Session ID | 2字节 | 0x8cfb | 会话ID |
| Length | 2字节 | PPP载荷长度 | 载荷长度 |

PPP头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Protocol | 2字节 | 0xc023 | PAP协议 |

PAP头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Code | 1字节 | 0x01 | Authenticate-Request |
| Identifier | 1字节 | 0x01 | 请求标识符 |
| Length | 2字节 | PAP包长度 | 包括头部和数据 |
| Peer-ID Length | 1字节 | 用户名长度 | 如: 10 |
| Peer-ID | 变长 | 用户名 | 明文用户名 |
| Password Length | 1字节 | 密码长度 | 如: 8 |
| Password | 变长 | 密码 | 明文密码 |

十六进制示例:
```
0000  28 6e d4 63 55 53 b0 25 aa 5b 26 c4 88 64 11 00
      │                 │                 │     │  │
      └─AC MAC          └─客户端MAC        │     │  └─Code(Session)
                                          │     └─Ver+Type
                                          └─类型(0x8864)

0010  8c fb 00 1e c0 23 01 01 00 1c 0a 32 30 32 33 31
      │     │     │     │  │  │     │  │
      │     │     │     │  │  │     │  └─用户名"2023112621"
      │     │     │     │  │  │     └─用户名长度(10)
      │     │     │     │  │  └─Length
      │     │     │     │  └─Identifier
      │     │     │     └─Code(Auth-Request)
      │     │     └─Protocol(PAP)
      │     └─Length
      └─Session ID(0x8cfb)

0020  31 32 36 32 31 08 70 61 73 73 77 6f 72 64
                        │  │
                        │  └─密码"password"(明文!)
                        └─密码长度(8)
```

安全警告: PAP认证中用户名和密码都是明文传输!
- 用户名: 2023112621 (可见)
- 密码: password (可见)
- 任何人抓包都能看到!

---

阶段7: IPCP Configure-Request数据包

功能: 请求IP地址和DNS服务器

以太网帧头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| 目标MAC地址 | 6字节 | AC的MAC | AC的MAC地址 |
| 源MAC地址 | 6字节 | 客户端MAC | 客户端MAC地址 |
| 类型 | 2字节 | 0x8864 | PPPoE Session |

PPPoE头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Version | 4位 | 1 | PPPoE版本 |
| Type | 4位 | 1 | PPPoE类型 |
| Code | 1字节 | 0x00 | Session Data |
| Session ID | 2字节 | 0x8cfb | 会话ID |
| Length | 2字节 | PPP载荷长度 | 载荷长度 |

PPP头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Protocol | 2字节 | 0x8021 | IPCP协议 |

IPCP头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Code | 1字节 | 0x01 | Configure-Request |
| Identifier | 1字节 | 0x01 | 请求标识符 |
| Length | 2字节 | IPCP包长度 | 包括头部和选项 |

IPCP Options:
- IP-Address (0x03): 请求的IP地址
- Primary-DNS (0x81): 主DNS服务器
- Secondary-DNS (0x83): 辅助DNS服务器

十六进制示例:
```
0000  28 6e d4 63 55 53 b0 25 aa 5b 26 c4 88 64 11 00
      │                 │                 │     │  │
      └─AC MAC          └─客户端MAC        │     │  └─Code(Session)
                                          │     └─Ver+Type
                                          └─类型(0x8864)

0010  8c fb 00 18 80 21 01 01 00 16 03 06 00 00 00 00
      │     │     │     │  │  │     │     │
      │     │     │     │  │  │     │     └─请求IP(0.0.0.0)
      │     │     │     │  │  │     └─IP-Address Option
      │     │     │     │  │  └─Length
      │     │     │     │  └─Identifier
      │     │     │     └─Code(Configure-Request)
      │     │     └─Protocol(IPCP)
      │     └─Length
      └─Session ID(0x8cfb)

0020  81 06 00 00 00 00 83 06 00 00 00 00
      │     │           │     │
      │     └─主DNS(0.0.0.0)  └─辅助DNS(0.0.0.0)
      └─Primary-DNS Option    └─Secondary-DNS Option
```

---

阶段8: IPCP Configure-Ack数据包

功能: AC分配IP地址和DNS服务器

以太网帧头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| 目标MAC地址 | 6字节 | 客户端MAC | 客户端MAC地址 |
| 源MAC地址 | 6字节 | AC的MAC | AC的MAC地址 |
| 类型 | 2字节 | 0x8864 | PPPoE Session |

PPPoE头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Version | 4位 | 1 | PPPoE版本 |
| Type | 4位 | 1 | PPPoE类型 |
| Code | 1字节 | 0x00 | Session Data |
| Session ID | 2字节 | 0x8cfb | 会话ID |
| Length | 2字节 | PPP载荷长度 | 载荷长度 |

PPP头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Protocol | 2字节 | 0x8021 | IPCP协议 |

IPCP头部:
| 字段 | 长度 | 值 | 含义 |
|------|------|-----|------|
| Code | 1字节 | 0x02 | Configure-Ack |
| Identifier | 1字节 | 0x01 | 对应请求的ID |
| Length | 2字节 | IPCP包长度 | 包括头部和选项 |

IPCP Options:
- IP-Address (0x03): 分配的IP地址
- Primary-DNS (0x81): 主DNS服务器
- Secondary-DNS (0x83): 辅助DNS服务器

十六进制示例:
```
0000  b0 25 aa 5b 26 c4 28 6e d4 63 55 53 88 64 11 00
      │                 │                 │     │  │
      └─客户端MAC        └─AC MAC          │     │  └─Code(Session)
                                          │     └─Ver+Type
                                          └─类型(0x8864)

0010  8c fb 00 18 80 21 02 01 00 16 03 06 0a a9 e3 a2
      │     │     │     │  │  │     │     │
      │     │     │     │  │  │     │     └─分配IP(10.169.227.162)
      │     │     │     │  │  │     └─IP-Address Option
      │     │     │     │  │  └─Length
      │     │     │     │  └─Identifier
      │     │     │     └─Code(Configure-Ack)
      │     │     └─Protocol(IPCP)
      │     └─Length
      └─Session ID(0x8cfb)

0020  81 06 ca 66 c0 44 83 06 3d 84 a3 44
      │     │           │     │
      │     └─主DNS      │     └─辅助DNS
      │   (202.102.192.68) (61.132.163.68)
      └─Primary-DNS Option  └─Secondary-DNS Option
```

至此,PPPoE拨号完成!客户端获得:
- IP地址: 10.169.227.162
- 主DNS: 202.102.192.68
- 辅助DNS: 61.132.163.68

---

五、各阶段数据包对比总结

| 阶段 | 以太网类型 | PPPoE Code | Session ID | PPP Protocol | 功能 |
|------|-----------|-----------|-----------|--------------|------|
| PADI | 0x8863 | 0x09 | 0x0000 | 无 | 广播寻找AC |
| PADO | 0x8863 | 0x07 | 0x0000 | 无 | AC响应 |
| PADR | 0x8863 | 0x19 | 0x0000 | 无 | 请求会话 |
| PADS | 0x8863 | 0x65 | 0x8cfb | 无 | 分配Session ID |
| LCP | 0x8864 | 0x00 | 0x8cfb | 0xc021 | 链路协商 |
| PAP | 0x8864 | 0x00 | 0x8cfb | 0xc023 | 身份认证 |
| IPCP | 0x8864 | 0x00 | 0x8cfb | 0x8021 | IP参数协商 |
| Session | 0x8864 | 0x00 | 0x8cfb | 0x0021 | 数据传输 |

关键转折点:
1. 以太网类型从0x8863变为0x8864 (PADS之后)
2. Session ID从0x0000变为0x8cfb (PADS分配)
3. PPPoE Code从各种值变为0x00 (进入Session阶段)

---

分析完成: 2025年11月25日
数据包文件: 2023112621.pcapng
说明: 本次抓包只包含Session阶段,其他阶段为理论分析
