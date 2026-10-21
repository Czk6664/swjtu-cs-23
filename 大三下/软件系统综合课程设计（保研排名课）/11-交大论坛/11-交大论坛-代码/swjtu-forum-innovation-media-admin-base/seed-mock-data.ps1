# Seed mock data into the running backend (http://localhost:8080/api)
# UTF-8 safe for Chinese payloads on Windows PowerShell 5.1.
$ErrorActionPreference = "Stop"
$base = "http://localhost:8080/api"

function Invoke-Api {
    param([string]$Method, [string]$Path, $Body, [string]$Token)
    $headers = @{}
    if ($Token) { $headers["Authorization"] = "Bearer $Token" }
    $uri = "$base$Path"
    if ($Body -ne $null) {
        $json = ($Body | ConvertTo-Json -Depth 6 -Compress)
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
        return Invoke-RestMethod -Uri $uri -Method $Method -Body $bytes -ContentType "application/json; charset=utf-8" -Headers $headers
    }
    return Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers
}

function Register-OrLogin {
    param($u)
    try {
        $r = Invoke-Api -Method Post -Path "/auth/register" -Body $u
        Write-Host "  registered: $($u.username)"
        return $r.data.token
    } catch {
        $login = @{ username = $u.username; password = $u.password }
        $r = Invoke-Api -Method Post -Path "/auth/login" -Body $login
        Write-Host "  exists, logged in: $($u.username)"
        return $r.data.token
    }
}

# --- 0. admin login ---
$adminTok = (Invoke-Api -Method Post -Path "/auth/login" -Body @{ username = "admin"; password = "admin123456" }).data.token
Write-Host "admin token len: $($adminTok.Length)"

# --- 1. users ---
$users = @(
    @{ username = "zhangwei";  password = "test123456"; email = "zhangwei@swjtu.local";  studentId = "2022110101"; college = "计算机与人工智能学院"; major = "软件工程" }
    @{ username = "lina";      password = "test123456"; email = "lina@swjtu.local";      studentId = "2022110202"; college = "电气工程学院";       major = "电气工程及其自动化" }
    @{ username = "wangfang";  password = "test123456"; email = "wangfang@swjtu.local";  studentId = "2021110303"; college = "交通运输与物流学院"; major = "交通运输" }
    @{ username = "chenhao";   password = "test123456"; email = "chenhao@swjtu.local";   studentId = "2023110404"; college = "机械工程学院";       major = "机械设计制造及其自动化" }
    @{ username = "liuyang";   password = "test123456"; email = "liuyang@swjtu.local";   studentId = "2022110505"; college = "经济管理学院";       major = "工商管理" }
    @{ username = "zhaoxin";   password = "test123456"; email = "zhaoxin@swjtu.local";   studentId = "2023110606"; college = "土木工程学院";       major = "土木工程" }
)
$tokens = @{}
Write-Host "`n[users]"
foreach ($u in $users) { $tokens[$u.username] = Register-OrLogin $u }

# --- 2. posts ---
# sectionId: 1 站务公告 2 课程互助 3 保研考研 4 实习就业 5 犀浦生活 6 二手闲置 7 失物招领
$posts = @(
    @{ by="zhangwei"; sectionId=2; title="数据结构期末复习资料分享"; content="整理了一份红黑树和B+树的复习笔记,包含手绘图解和真题解析,需要的同学评论区留邮箱。复习重点:平衡因子的维护、旋转操作、以及与数据库索引的关系。"; tags=@("数据结构","期末复习","计算机") }
    @{ by="lina"; sectionId=2; title="电路分析这门课怎么学才不挂科"; content="戴维南定理和诺顿定理一直搞不懂,有没有学长学姐能讲讲做题思路?特别是含受控源的电路怎么求等效电阻。"; tags=@("电路分析","求助") }
    @{ by="wangfang"; sectionId=3; title="2026交通运输考研经验贴(初试410分)"; content="本人成功上岸,分享一下专业课和数学的复习节奏。数学一定要早做真题,专业课交通工程学要结合规范理解。政治跟着肖秀荣冲刺就行。"; tags=@("考研","经验贴","交通运输") }
    @{ by="chenhao"; sectionId=3; title="保研夏令营都需要准备什么材料"; content="想冲一下本校和电子科大的夏令营,简历、成绩单、推荐信这些怎么准备?英语六级500够吗?"; tags=@("保研","夏令营") }
    @{ by="liuyang"; sectionId=4; title="字节跳动暑期实习面经(数据分析岗)"; content="三轮技术面+一轮HR面,问了SQL窗口函数、AB实验设计、还有一道用户增长的开放题。整体不难但很看业务sense,准备好项目细节就行。"; tags=@("实习","面经","字节跳动") }
    @{ by="zhaoxin"; sectionId=4; title="土木行业还值得去吗?求过来人指点"; content="大三了对未来很迷茫,设计院和施工单位待遇都不太理想,有没有转行做选调或者考公的学长分享下经验?"; tags=@("就业","土木","迷茫") }
    @{ by="lina"; sectionId=5; title="犀浦校区哪家food最好吃"; content="新生求推荐!食堂二楼的麻辣香锅和东门外的冒菜哪个更值得去?预算控制在20以内。"; tags=@("犀浦","美食","生活") }
    @{ by="chenhao"; sectionId=5; title="犀浦到成都市区怎么走最快"; content="周末想去春熙路玩,地铁6号线转1号线大概要多久?有没有更省时间的路线?"; tags=@("交通","犀浦","出行") }
    @{ by="zhangwei"; sectionId=6; title="出一台九成新的机械键盘"; content="自用Cherry青轴,买来半年,因为换了客制化所以出掉。原价399现在200出,犀浦校区可当面交易。"; tags=@("二手","键盘") }
    @{ by="liuyang"; sectionId=6; title="转让考研全套政治资料"; content="今年刚考完,肖四肖八、徐涛核心考案、还有腿姐冲刺背诵手册,全套50打包,无笔记基本全新。"; tags=@("二手","考研资料") }
    @{ by="wangfang"; sectionId=7; title="在图书馆三楼捡到一张校园卡"; content="姓名打码了,卡号尾号3721,失主请到图书馆服务台认领,或者私信我核对信息。"; tags=@("失物招领","校园卡") }
    @{ by="zhaoxin"; sectionId=7; title="丢了一把黑色雨伞求好心人"; content="昨天下午在教学楼一区103教室落了一把全自动黑伞,伞柄有划痕,捡到的同学麻烦联系我,有偿感谢。"; tags=@("寻物","雨伞") }
)
Write-Host "`n[posts]"
$postIds = @()
foreach ($p in $posts) {
    $tok = $tokens[$p.by]
    $body = @{ title=$p.title; content=$p.content; sectionId=$p.sectionId; tags=$p.tags }
    $r = Invoke-Api -Method Post -Path "/posts" -Body $body -Token $tok
    $postId = $r.data.id; $st = $r.data.status
    $postIds += $postId
    Write-Host ("  post #{0} status={1} by {2}: {3}" -f $postId, $st, $p.by, $p.title)
    # if pending review, approve as admin (status 1 = published)
    if ($st -ne 1) {
        try { Invoke-Api -Method Patch -Path "/posts/$postId/status" -Body @{ status = 1 } -Token $adminTok | Out-Null; Write-Host "    -> approved by admin" } catch { Write-Host "    -> approve failed: $($_.Exception.Message)" }
    }
}

# --- 3. comments (cross-user) ---
Write-Host "`n[comments]"
$comments = @(
    @{ post=0; by="lina";     text="太及时了!求一份笔记,邮箱lina@swjtu.local,谢谢大佬!" }
    @{ post=0; by="chenhao";  text="红黑树那块讲得很清楚,收藏了。" }
    @{ post=2; by="chenhao";  text="恭喜上岸!想问下专业课参考书是哪个版本?" }
    @{ post=2; by="zhangwei"; text="410太强了,膜拜学长。" }
    @{ post=4; by="zhaoxin";  text="AB实验那题能展开说说吗?面试也被问到过。" }
    @{ post=4; by="wangfang"; text="感谢分享,正好准备投数据岗。" }
    @{ post=6; by="zhangwei"; text="麻辣香锅yyds,记得加午餐肉。" }
    @{ post=6; by="liuyang";  text="东门冒菜性价比更高,推荐!" }
    @{ post=10; by="liuyang"; text="好人一生平安,帮顶。" }
)
foreach ($c in $comments) {
    $postId = $postIds[$c.post]; $tok = $tokens[$c.by]
    try { $r = Invoke-Api -Method Post -Path "/posts/$postId/comments" -Body @{ content=$c.text } -Token $tok; Write-Host "  comment on #$postId by $($c.by) ok" } catch { Write-Host "  comment failed on #$postId : $($_.Exception.Message)" }
}

# --- 4. likes & favorites (cross-user) ---
Write-Host "`n[likes/favorites]"
$likeMap = @(
    @{ post=0; users=@("lina","chenhao","liuyang","wangfang") }
    @{ post=2; users=@("chenhao","zhangwei","lina","zhaoxin","liuyang") }
    @{ post=4; users=@("zhaoxin","wangfang","zhangwei") }
    @{ post=6; users=@("zhangwei","liuyang") }
    @{ post=8; users=@("lina","chenhao") }
)
foreach ($lm in $likeMap) {
    $postId = $postIds[$lm.post]
    foreach ($un in $lm.users) {
        try { Invoke-Api -Method Post -Path "/posts/$postId/like" -Token $tokens[$un] | Out-Null } catch {}
    }
    Write-Host "  liked #$postId by $($lm.users.Count) users"
}
$favMap = @( @{post=2; users=@("chenhao","zhangwei")}, @{post=4; users=@("zhaoxin")}, @{post=0; users=@("lina")} )
foreach ($fm in $favMap) {
    $postId = $postIds[$fm.post]
    foreach ($un in $fm.users) { try { Invoke-Api -Method Post -Path "/posts/$postId/favorite" -Token $tokens[$un] | Out-Null } catch {} }
    Write-Host "  favorited #$postId by $($fm.users.Count) users"
}

# --- 5. check-ins (growth) ---
Write-Host "`n[check-ins]"
foreach ($un in @("zhangwei","lina","wangfang","chenhao")) {
    try { Invoke-Api -Method Post -Path "/growth/check-in" -Token $tokens[$un] | Out-Null; Write-Host "  $un checked in" } catch { Write-Host "  $un check-in: $($_.Exception.Message)" }
}

Write-Host "`nDONE. Seeded $($postIds.Count) posts, $($users.Count) users."
