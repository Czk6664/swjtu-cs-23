# 一次性口令机制（OTP）验证实验

## 一、实验名称

一次性口令机制（OTP）验证实验。

## 二、实验目的

1. 理解静态口令与一次性口令在认证安全性上的差异，重点理解重放攻击为什么会对静态口令造成威胁。
2. 掌握共享口令表型、序列 / 计数器同步型、时间同步型三类典型 OTP。
3. 掌握认证端生成 OTP、验证端重算并比较、状态推进与日志记录的完整流程。
4. 验证 OTP 对重放攻击的抵抗能力，并分析同步误差、口令复用、篡改消息等异常场景。
5. 基于实验现象总结 OTP 的安全边界：增强认证与新鲜性，不直接等价于通信保密。

## 三、实验原理

静态口令每次提交相同秘密，服务器只做固定值比较时，攻击者截获一次合法认证消息后可以完整重放。一次性口令把认证值与口令表位置、计数器或时间槽绑定，服务器验证成功后推进状态或记录已用标记，使旧消息再次提交时被判定为复用失败、新鲜性失败或比较失败。

共享口令表型 OTP 要求客户端和服务器保存相同口令表并同步当前位置；计数器型 OTP 使用共享密钥和 counter 派生口令，并可通过 look_ahead 滑动窗口处理轻微超前；时间同步型 OTP 使用共享密钥和时间槽派生口令，并通过 allowed_window 容忍小幅时钟偏差。

## 四、实验环境

- 操作系统：Windows / Linux / macOS 均可。
- 编程语言：Python 3.x，本次运行环境为 Python 3.13.5。
- 开发工具：PyCharm、VS Code、Jupyter Notebook 或命令行均可。

## 五、程序设计

程序采用模块化结构：`common.py` 负责用户标识规范化、HMAC 派生、OTP 截断、恒定时间比较、复用检查和日志记录；`static_password_baseline.py`、`otp_list_mode.py`、`otp_counter_mode.py`、`otp_time_mode.py` 分别实现对照模式与三类 OTP；`attack_simulation.py` 负责重放、篡改和漂移模拟；`main.py` 负责组织实验用例并生成报告。

实验公共参数：

- 用户：`u01`，`u02`（用于时间同步模式干净测试）。
- 口令表：`L=[111111,222222,333333,444444,555555]`，初始 `pos=0`。
- 计数器模式：初始 `counter=0`；服务器验证窗口 `look_ahead=3`。
- 时间同步模式：`step=30s`，`allowed_window=1`（允许 ±1 个时间槽）；基准时间戳 `t0=1700000000`。

## 六、实验结果

### 实验 A：静态口令对照 (Baseline)

| 用例编号 | 操作描述 | 测试输入 | 预期结果 | 实际输出与分析 | 结果判定 |
| --- | --- | --- | --- | --- | --- |
| TC-A1 | 正常认证 | (u01, "static_pass") | 通过 | a. 返回值：success=True，错误码：OK。b. 服务器状态：静态口令模式无 pos/counter/used slot 状态推进。c. 日志字段：user=u01, mode=static, result=pass, reason=none。 | 一致。口令正确，因此认证通过。 |
| TC-A2 | 错误口令 | (u01, "wrong_pass") | 拒绝：比较失败 | a. 返回值：success=False，错误码：PASSWORD_MISMATCH。b. 服务器状态：无状态变化。c. 日志字段：user=u01, mode=static, result=reject, reason=比较失败。 | 一致。提交口令与服务器保存口令不一致。 |
| TC-A3 | 重放攻击 | 截获 TC-A1 的消息 (id=u01, pass="static_pass") 再次提交 | 通过 | a. 返回值：success=True，错误码：OK。b. 服务器状态：无已用记录，无状态推进。c. 日志字段：user=u01, mode=static, result=pass, attack=replay。 | 一致。静态口令缺少新鲜性检查，旧认证消息仍可通过。 |

### 实验 B：共享口令表型 OTP

| 用例编号 | 操作描述 | 测试输入 | 预期结果 | 实际输出与分析 | 结果判定 |
| --- | --- | --- | --- | --- | --- |
| TC-B1 | 正常认证，使用 pos=0 的口令 | (u01, 111111, pos=0) | 通过 | a. 返回值：success=True，错误码：OK。b. 服务器状态：pos: 0 → 1。c. 日志字段：user=u01, mode=list, received_otp=111111, expected_otp=111111, pos=0, result=pass。 | 一致。提交 OTP 与当前位置口令一致。 |
| TC-B2 | 重放攻击 | 重放 TC-B1 的消息 (id=u01, otp="111111") | 拒绝：复用失败 | a. 返回值：success=False，错误码：OTP_REUSED_OR_EXPIRED。b. 服务器状态：当前 pos=1，保持不变。c. 日志字段：user=u01, mode=list, received_otp=111111, current_pos=1, expected_otp=222222, result=reject, reason=复用失败。 | 一致。旧位置口令已使用，重放被拒绝。 |
| TC-B3 | 篡改 OTP | (u01, "999999")，当前服务器 pos=1 | 拒绝：比较失败 | a. 返回值：success=False，错误码：OTP_MISMATCH。b. 服务器状态：pos=1，不推进。c. 日志字段：user=u01, mode=list, received_otp=999999, expected_otp=222222, result=reject, reason=比较失败。 | 一致。篡改后的 OTP 与服务器期望值不一致。 |
| TC-B4 | 指针失步，客户端超前 1 位 | client pos=2, server pos=1 | 拒绝：新鲜性失败 | a. 返回值：success=False，错误码：POSITION_OUT_OF_SYNC。b. 服务器状态：server_pos=1，不推进。c. 日志字段：user=u01, mode=list, client_pos=2, server_pos=1, received_otp=333333, expected_otp=222222, result=reject, reason=新鲜性失败。 | 一致。客户端和服务器位置不同步，当前口令不新鲜。 |

### 实验 C：计数器/序列同步型 OTP

| 用例编号 | 操作描述 | 测试输入 | 预期结果 | 实际输出与分析 | 结果判定 |
| --- | --- | --- | --- | --- | --- |
| TC-C0 | 生成规则自检 | 1. 用 c=5 生成两次；2. 用 c=5 和 c=6 生成 | 通过 | a. 返回值：success=True，错误码：SELF_CHECK_OK。b. 服务器状态：自检不改变服务器 counter。c. 日志字段：mode=counter, c5_repeat_equal=True, c5_c6_equal=False, result=pass。 | 一致。同一计数器输出一致，不同计数器输出不同。 |
| TC-C1 | 正常认证 | (u01, otp_c0, counter=0) | 通过 | a. 返回值：success=True，错误码：OK。b. 服务器状态：counter: 0 → 1。c. 日志字段：user=u01, mode=counter, received_counter=0, server_counter=0, result=pass。 | 一致。客户端 counter 与服务器 counter 一致。 |
| TC-C2 | 重放攻击 | 重放 TC-C1 的消息 (c=0) | 拒绝：复用失败 | a. 返回值：success=False，错误码：COUNTER_REUSED。b. 服务器状态：当前 counter=1，保持不变。c. 日志字段：user=u01, mode=counter, received_counter=0, server_counter=1, result=reject, reason=复用失败。 | 一致。counter=0 已经使用，旧消息被拒绝。 |
| TC-C3 | 窗口内漂移 | server=1, client=3 | 通过 | a. 返回值：success=True，错误码：OK_WITH_RESYNC。b. 服务器状态：counter: 1 → 4。c. 日志字段：user=u01, mode=counter, server_counter=1, received_counter=3, look_ahead=3, allowed_range=1-4, result=pass。 | 一致。客户端计数器在允许窗口内，因此通过并推进服务器状态。 |
| TC-C4 | 窗口外漂移 | server=4, client=10 | 拒绝：新鲜性失败 | a. 返回值：success=False，错误码：COUNTER_OUT_OF_WINDOW。b. 服务器状态：counter=4，不推进。c. 日志字段：user=u01, mode=counter, server_counter=4, received_counter=10, look_ahead=3, allowed_range=4-7, result=reject, reason=新鲜性失败。 | 一致。客户端计数器超出允许窗口。 |
| TC-C5 | 篡改 counter 字段 | otp 对应 c=4，但传 c=2 | 拒绝：比较失败 | a. 返回值：success=False，错误码：OTP_COUNTER_MISMATCH。b. 服务器状态：counter 不推进。c. 日志字段：user=u01, mode=counter, otp_generated_counter=4, received_counter=2, result=reject, reason=比较失败。 | 一致。OTP 与 counter 不匹配，服务器重算结果不同。 |

### 实验 D：时间同步型 OTP

| 用例编号 | 操作描述 | 测试输入 | 预期结果 | 实际输出与分析 | 结果判定 |
| --- | --- | --- | --- | --- | --- |
| TC-D0 | 生成规则自检 | 1. 同一 timestamp 生成两次；2. t0 和 t0+30 分别生成 | 通过 | a. 返回值：success=True，错误码：SELF_CHECK_OK。b. 服务器状态：自检不改变已用 slot。c. 日志字段：mode=time, same_timestamp_equal=True, different_slot_equal=False, result=pass。 | 一致。同一时间戳生成结果相同，不同时间槽生成结果不同。 |
| TC-D1 | 正常窗口内 | 客户端 ts=t0，服务器 ts=t0 | 通过 | a. 返回值：success=True，错误码：OK。b. 服务器状态：记录 used_slot[u01]=56666666。c. 日志字段：user=u01, mode=time, received_ts=1700000000, client_slot=56666666, server_slot=56666666, result=pass。 | 一致。客户端和服务器处于同一时间槽。 |
| TC-D2 | 重放攻击 | 重放 TC-D1 的消息 | 拒绝：复用失败 | a. 返回值：success=False，错误码：TIME_SLOT_REUSED。b. 服务器状态：used_slot[u01]=56666666 已存在，不改变。c. 日志字段：user=u01, mode=time, slot=56666666, result=reject, reason=复用失败。 | 一致。该时间槽已经使用，重放被拒绝。 |
| TC-D3 | 允许窗口测试，±1 槽 | 用户 u02，客户端 ts=t0，服务器 ts=t0+30 | 通过 | a. 返回值：success=True，错误码：OK_WITH_TIME_WINDOW。b. 服务器状态：记录 used_slot[u02]=56666666。c. 日志字段：user=u02, mode=time, client_slot=56666666, server_slot=56666667, slot_delta=1, allowed_window=1, result=pass。 | 一致。时间偏差为 1 个时间槽，在允许窗口内。 |
| TC-D4 | 窗口外，过期 | 客户端 ts=t0-60，服务器 ts=t0 | 拒绝：新鲜性失败 | a. 返回值：success=False，错误码：TIME_SLOT_OUT_OF_WINDOW。b. 服务器状态：不记录新的 used_slot。c. 日志字段：user=u01, mode=time, client_slot=56666664, server_slot=56666666, slot_delta=2, allowed_window=1, result=reject, reason=新鲜性失败。 | 一致。客户端时间槽过期，超出允许窗口。 |
| TC-D5 | 篡改 timestamp | 客户端生成 ts=t0 的 OTP，后将消息中 timestamp 改为 t0+60 | 拒绝：比较失败 | a. 返回值：success=False，错误码：OTP_TIMESTAMP_MISMATCH。b. 服务器状态：不记录新的 used_slot。c. 日志字段：user=u01, mode=time, otp_original_slot=56666666, received_slot=56666668, result=reject, reason=比较失败。 | 一致。OTP 与被篡改后的 timestamp 不匹配。 |

### 实验 E/F：统一安全性用例与模式比较

#### 统一攻击模型

| 用例编号 | 攻击类型 | 测试说明 | 口令表 | 计数器 | 时间 OTP | 原因 |
| --- | --- | --- | --- | --- | --- | --- |
| TC-S1 | 身份篡改 | id 错误但 OTP 正确 | 拒绝：比较失败 | 拒绝：比较失败 | 拒绝：比较失败 | 错误 id 会导致服务器读取错误用户的密钥或状态，重算 OTP 不一致。 |
| TC-S2 | OTP 篡改 | OTP 错误，同步字段正确 | 拒绝：比较失败 | 拒绝：比较失败 | 拒绝：比较失败 | OTP 被修改后，与服务器重算值不一致。 |
| TC-S3 | 重放攻击 | 完整重放已通过消息 | 拒绝：复用失败 | 拒绝：复用失败 | 拒绝：复用失败 | 口令表位置、计数器或时间槽已经被使用。 |
| TC-S4 | 同步字段篡改 | 改 counter / ts | 拒绝：新鲜性失败 | 拒绝：比较失败 | 拒绝：比较失败 | 同步字段改变后，OTP 与状态字段不匹配；口令表型表现为当前位置不一致。 |
| TC-S5 | 绑定性破坏 | OTP 与 counter / ts 不匹配 | 拒绝：比较失败 | 拒绝：比较失败 | 拒绝：比较失败 | OTP 必须与身份、计数器或时间槽绑定，绑定关系破坏后验证失败。 |

#### 模式安全性对比

| 安全属性 | 口令表 | 计数器 | 时间 OTP |
| --- | --- | --- | --- |
| 防重放 | 通过。成功后 pos 推进，旧口令无法再次使用。 | 通过。成功后 counter 推进，旧 counter 被拒绝。 | 通过。成功后记录已用 slot，同一时间槽不能重复使用。 |
| 状态依赖 | 强。必须保存并维护当前 pos。 | 强。必须保存并维护服务器端 counter。 | 中等。需要时间窗口判断，并建议保存已用 slot。 |
| 同步要求 | 高。客户端和服务器 pos 必须一致。 | 中等。允许通过 look_ahead 处理轻微超前。 | 中等。允许通过 allowed_window 处理轻微时钟偏差。 |
| 容错能力 | 较弱。指针失步后容易失败。 | 较强。窗口内漂移可以通过并重同步。 | 较强。窗口内时间偏差可以通过。 |
| 实现复杂度 | 较低。规则简单，但口令表管理不灵活。 | 中等。需要密钥、计数器、窗口和状态推进。 | 中等偏高。需要时间槽、时钟窗口和已用 slot 记录。 |

## 七、结果分析

1. 静态口令不维护新鲜性状态，TC-A3 中完整重放仍能通过。
2. 共享口令表型 OTP 成功后推进 `pos`，旧位置口令和指针失步都会被拒绝。
3. 计数器型 OTP 绑定 `counter`，窗口内漂移可以通过并同步服务器状态，窗口外漂移被拒绝。
4. 时间同步型 OTP 绑定时间槽，允许窗口内时钟偏差，但已用 slot 不能重复使用。
5. OTP 增强的是认证与新鲜性，不直接提供通信保密；真实系统仍需要 TLS、完整性保护、限速和审计。

## 八、运行方法

在实验目录执行：

```bash
python -m otp_lab.main
```

运行后会生成 `otp_lab/logs/events.jsonl` 和 `otp_lab_report.md`。
