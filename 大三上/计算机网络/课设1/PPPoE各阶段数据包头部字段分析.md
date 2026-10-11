# PPPoE 各阶段数据包头部字段详细分析

## 一、PPPoE Discovery 阶段（发现阶段）

### 1. PADI 数据包分析（数据包 #1）

#### 以太网帧头部
```
目标 MAC 地址 (Destination): ff:ff:ff:ff:ff:ff (广播地址)
源 MAC 地址 (Source):        b0:25:aa:5b:26:c4 (客户端)
类型 (Type):                 0x8863 (PPPoE Discovery)
```

**字段说明**:
- **目标 MAC**: 广播地址，用于在局域网中寻找所有可用的 AC
- **源 MAC**: 客户端网卡的物理地址
- **类型**: 0x8863 表示这是 PPPoE 发现阶段的数据包

#### PPPoE 头部
```
版本 (Version):    1
类型 (Type):       1
代码 (Code):       0x09 (PADI - PPPoE Active Discovery Initiation)
会话 ID (Session): 0x0000
长度 (Length):     20 字节
```

**字段说明**:
- **Version**: PPPoE 协议版本，固定为 1
- **Type**: PPPoE 类型，固定为 1
- **Code**: 0x09 表示 PADI，客户端发起发现请求
- **Session ID**: 0x0000，发现阶段会话 ID 必须为 0
- **Length**: PPPoE 载荷长度（Tag 列表的总长度）

#### PPPoE Tag 列表
```
Tag 1:
  Tag Type:  0x0101 (Service-Name)
  Tag Length: 0
  Tag Value:  空 (请求任何可用服务)

Tag 2:
  Tag Type:  0x0103 (Host-Uniq)
  Tag Length: 12
  Tag Value:  04 00 00 00 00 00 00 00 07 00 00 00
```

**字段说明**:
- **Service-Name Tag**: 空值表示客户端请求任何可用的服务
- **Host-Uniq Tag**: 主机唯一标识符，用于匹配响应

---

### 2. PADO 数据包分析（数据包 #2）

#### 以太网帧头部
```
目标 MAC 地址: b0:25:aa:5b:26:c4 (客户端，单播)
源 MAC 地址:   00:00:5e:00:01:01 (AC 服务器)
类型:          0x8863 (PPPoE Discovery)
```

**字段说明**:
- **目标 MAC**: 单播发送给发起请求的客户端
- **源 MAC**: AC（访问集中器）的物理地址

#### PPPoE 头部
```
版本:     1
类型:     1
代码:     0x07 (PADO - PPPoE Active Discovery Offer)
会话 ID:  0x0000
长度:     37 字节
```

**字段说明**:
- **Code**: 0x07 表示 PADO，AC 提供服务响应
- **Session ID**: 仍为 0x0000，会话尚未建立

#### PPPoE Tag 列表
```
Tag 1:
  Tag Type:  0x0101 (Service-Name)
  Tag Length: 0
  Tag Value:  空

Tag 2:
  Tag Type:  0x0103 (Host-Uniq)
  Tag Length: 12
  Tag Value:  04 00 00 00 00 00 00 00 07 00 00 00

Tag 3:
  Tag Type:  0x0102 (AC-Name)
  Tag Length: 13
  Tag Value:  "X-XNJD-ME60-1"
```

**字段说明**:
- **AC-Name Tag**: 访问集中器的名称，标识服务器身份
- **Host-Uniq Tag**: 回显客户端的唯一标识符

---

### 3. PADR 数据包分析（数据包 #3）

#### 以太网帧头部
```
目标 MAC 地址: 00:00:5e:00:01:01 (选定的 AC，单播)
源 MAC 地址:   b0:25:aa:5b:26:c4 (客户端)
类型:          0x8863 (PPPoE Discovery)
```

**字段说明**:
- **目标 MAC**: 客户端选定的 AC 地址（单播）

#### PPPoE 头部
```
版本:     1
类型:     1
代码:     0x19 (PADR - PPPoE Active Discovery Request)
会话 ID:  0x0000
长度:     20 字节
```

**字段说明**:
- **Code**: 0x19 表示 PADR，客户端请求建立会话
- **Session ID**: 仍为 0x0000

#### PPPoE Tag 列表
```
Tag 1:
  Tag Type:  0x0101 (Service-Name)
  Tag Length: 0
  Tag Value:  空

Tag 2:
  Tag Type:  0x0103 (Host-Uniq)
  Tag Length: 12
  Tag Value:  04 00 00 00 00 00 00 00 08 00 00 00
```

---

### 4. PADS 数据包分析（数据包 #4）

#### 以太网帧头部
```
目标 MAC 地址: b0:25:aa:5b:26:c4 (客户端，单播)
源 MAC 地址:   00:00:5e:00:01:01 (AC 服务器)
类型:          0x8863 (PPPoE Discovery)
```

#### PPPoE 头部
```
版本:     1
类型:     1
代码:     0x65 (PADS - PPPoE Active Discovery Session-confirmation)
会话 ID:  0x57a3 (22435 十进制) ⭐ 重要！
长度:     20 字节
```

**字段说明**:
- **Code**: 0x65 表示 PADS，AC 确认会话建立
- **Session ID**: 0x57a3，AC 分配的唯一会话标识符，后续所有数据包都使用此 ID

#### PPPoE Tag 列表
```
Tag 1:
  Tag Type:  0x0101 (Service-Name)
  Tag Length: 0
  Tag Value:  空

Tag 2:
  Tag Type:  0x0103 (Host-Uniq)
  Tag Length: 12
  Tag Value:  04 00 00 00 00 00 00 00 08 00 00 00
```

---

## 二、PPPoE Session 阶段（会话阶段）

### Ⅰ. LCP 协商阶段（数据包 #5）

#### 以太网帧头部
```
目标 MAC 地址: b0:25:aa:5b:26:c4 (客户端)
源 MAC 地址:   00:00:5e:00:01:01 (AC 服务器)
类型:          0x8864 (PPPoE Session) ⭐ 注意类型变化
```

**字段说明**:
- **类型**: 0x8864 表示 PPPoE 会话阶段（不再是 0x8863）

#### PPPoE 头部
```
版本:     1
类型:     1
代码:     0x00 (Session Data)
会话 ID:  0x57a3 (22435) ⭐ 使用之前分配的会话 ID
长度:     20 字节
```

**字段说明**:
- **Code**: 0x00 表示会话数据传输
- **Session ID**: 使用 PADS 中分配的会话 ID

#### PPP 头部
```
协议 (Protocol): 0xc021 (LCP - Link Control Protocol)
```

**字段说明**:
- **Protocol**: 0xc021 表示 LCP 协议

#### LCP 数据包
```
代码 (Code):        0x01 (Configure-Request)
标识符 (ID):        0x01
长度 (Length):      18 字节
选项 (Options):
  Option 1:
    类型:   0x01 (Maximum-Receive-Unit)
    长度:   4
    值:     1492 (MTU 大小)
  
  Option 2:
    类型:   0x03 (Authentication-Protocol)
    长度:   4
    值:     0xc023 (PAP - Password Authentication Protocol)
  
  Option 3:
    类型:   0x05 (Magic-Number)
    长度:   6
    值:     2747322348
```

**字段说明**:
- **Code**: 0x01 表示配置请求
- **MRU**: 最大接收单元为 1492 字节（以太网 MTU 1500 - PPPoE 头部 8 字节）
- **Authentication-Protocol**: 使用 PAP 认证
- **Magic-Number**: 用于检测环路

---

### Ⅱ. 认证阶段（PAP 认证）

#### PAP Request 数据包结构
```
以太网头部:
  目标 MAC: AC 地址
  源 MAC:   客户端地址
  类型:     0x8864

PPPoE 头部:
  版本:     1
  类型:     1
  代码:     0x00
  会话 ID:  0x57a3
  长度:     [根据载荷计算]

PPP 头部:
  协议:     0xc023 (PAP)

PAP 数据:
  代码:     0x01 (Authenticate-Request)
  ID:       [序号]
  长度:     [总长度]
  Peer-ID Length:   [用户名长度]
  Peer-ID:          [用户名，明文] ⚠️ 安全风险
  Password Length:  [密码长度]
  Password:         [密码，明文] ⚠️ 安全风险
```

**安全警告**: PAP 以明文传输用户名和密码，存在严重安全隐患！

---

### Ⅲ. IPCP 协商阶段

#### IPCP Configure-Request 数据包
```
以太网头部:
  类型: 0x8864

PPPoE 头部:
  会话 ID: 0x57a3

PPP 头部:
  协议: 0x8021 (IPCP - IP Control Protocol)

IPCP 数据:
  代码:   0x01 (Configure-Request)
  ID:     [序号]
  长度:   [总长度]
  选项:
    Option 1:
      类型: 0x03 (IP-Address)
      长度: 6
      值:   0.0.0.0 (请求分配 IP)
    
    Option 2:
      类型: 0x81 (Primary-DNS)
      长度: 6
      值:   0.0.0.0 (请求 DNS 服务器地址)
    
    Option 3:
      类型: 0x83 (Secondary-DNS)
      长度: 6
      值:   0.0.0.0 (请求备用 DNS)
```

#### IPCP Configure-Ack 数据包
```
PPP 头部:
  协议: 0x8021 (IPCP)

IPCP 数据:
  代码:   0x02 (Configure-Ack)
  ID:     [与 Request 相同]
  长度:   [总长度]
  选项:
    Option 1:
      类型: 0x03 (IP-Address)
      长度: 6
      值:   10.169.130.164 ⭐ 分配的 IP 地址
    
    Option 2:
      类型: 0x81 (Primary-DNS)
      长度: 6
      值:   223.5.5.5 (阿里 DNS)
```

---

## 三、完整头部字段总结表

### PPPoE Discovery 阶段头部字段

| 字段 | PADI | PADO | PADR | PADS |
|------|------|------|------|------|
| **以太网目标 MAC** | 广播 | 客户端 | AC | 客户端 |
| **以太网源 MAC** | 客户端 | AC | 客户端 | AC |
| **以太网类型** | 0x8863 | 0x8863 | 0x8863 | 0x8863 |
| **PPPoE 版本** | 1 | 1 | 1 | 1 |
| **PPPoE 类型** | 1 | 1 | 1 | 1 |
| **PPPoE 代码** | 0x09 | 0x07 | 0x19 | 0x65 |
| **会话 ID** | 0x0000 | 0x0000 | 0x0000 | 0x57a3 |
| **主要 Tag** | Service-Name<br>Host-Uniq | Service-Name<br>Host-Uniq<br>AC-Name | Service-Name<br>Host-Uniq | Service-Name<br>Host-Uniq |

### PPPoE Session 阶段头部字段

| 字段 | LCP | PAP | IPCP |
|------|-----|-----|------|
| **以太网类型** | 0x8864 | 0x8864 | 0x8864 |
| **PPPoE 代码** | 0x00 | 0x00 | 0x00 |
| **会话 ID** | 0x57a3 | 0x57a3 | 0x57a3 |
| **PPP 协议** | 0xc021 | 0xc023 | 0x8021 |
| **主要功能** | 链路配置<br>MTU: 1492<br>认证: PAP | 用户认证<br>明文传输 | IP 配置<br>IP: 10.169.130.164<br>DNS: 223.5.5.5 |

---

## 四、关键字段含义详解

### 1. PPPoE Code 字段
- **0x09 (PADI)**: 客户端发起发现，寻找 AC
- **0x07 (PADO)**: AC 提供服务响应
- **0x19 (PADR)**: 客户端请求建立会话
- **0x65 (PADS)**: AC 确认会话，分配 Session ID
- **0x00 (Session)**: 会话数据传输

### 2. Session ID 字段
- **Discovery 阶段**: 必须为 0x0000
- **Session 阶段**: 使用 PADS 分配的唯一 ID (本例: 0x57a3)
- **作用**: 区分不同的 PPPoE 会话

### 3. PPP Protocol 字段
- **0xc021**: LCP（链路控制协议）
- **0xc023**: PAP（密码认证协议）
- **0xc223**: CHAP（挑战握手认证协议）
- **0x8021**: IPCP（IP 控制协议）
- **0x0021**: IP 数据包

### 4. LCP Options
- **Type 0x01 (MRU)**: 最大接收单元，通常为 1492
- **Type 0x03 (Auth)**: 认证协议类型
- **Type 0x05 (Magic)**: 魔术数字，检测环路

### 5. IPCP Options
- **Type 0x03**: IP 地址
- **Type 0x81**: 主 DNS 服务器
- **Type 0x83**: 备用 DNS 服务器

---

## 五、数据包流程图

```
客户端                                    AC 服务器
  |                                          |
  |  PADI (广播, Session ID=0)              |
  |----------------------------------------->|
  |                                          |
  |  PADO (单播, Session ID=0, AC-Name)     |
  |<-----------------------------------------|
  |                                          |
  |  PADR (单播, Session ID=0)              |
  |----------------------------------------->|
  |                                          |
  |  PADS (单播, Session ID=0x57a3) ⭐      |
  |<-----------------------------------------|
  |                                          |
  |===== Discovery 阶段结束，Session 开始 =====|
  |                                          |
  |  LCP Configure-Request (MRU, Auth)      |
  |<---------------------------------------->|
  |  LCP Configure-Ack                      |
  |                                          |
  |  PAP Authenticate-Request (明文)        |
  |----------------------------------------->|
  |  PAP Authenticate-Ack                   |
  |<-----------------------------------------|
  |                                          |
  |  IPCP Configure-Request (IP=0.0.0.0)    |
  |----------------------------------------->|
  |  IPCP Configure-Ack (IP=10.169.130.164) |
  |<-----------------------------------------|
  |                                          |
  |===== PPPoE 连接建立完成，开始传输数据 =====|
```

---

## 六、实际抓包数据对照

### 本次分析的关键参数
- **客户端 MAC**: b0:25:aa:5b:26:c4
- **AC MAC**: 00:00:5e:00:01:01
- **AC 名称**: X-XNJD-ME60-1
- **Session ID**: 0x57a3 (22435)
- **分配 IP**: 10.169.130.164
- **MTU**: 1492 字节
- **认证方式**: PAP（不安全）
- **DNS**: 223.5.5.5（阿里 DNS）

---

**报告完成时间**: 2025年11月25日  
**数据包文件**: 2023112621.pcapng  
**分析工具**: Scapy
