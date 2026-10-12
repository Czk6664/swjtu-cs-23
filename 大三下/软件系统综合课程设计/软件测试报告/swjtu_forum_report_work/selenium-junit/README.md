# 西南交大校园论坛 Selenium/JUnit 测试脚本

## 运行前提

1. 先启动便携版系统：`D:\大三下\软件系统综合课程设计\课设\jiaodaluntan\release\swjtu-forum-portable\start.bat`
2. 确认前端可访问：`http://localhost:4173`
3. 确认本机安装 Chrome；脚本默认使用 `C:\Program Files\Google\Chrome\Application\chrome.exe`
4. 在 Eclipse 中以 Maven Project 导入本目录，或在命令行执行：

```powershell
mvn test
```

脚本使用 Selenium 4 自带 Selenium Manager 自动准备 ChromeDriver。若实验机无法联网下载驱动，可手动下载与 Chrome 版本匹配的 chromedriver，并在运行参数中配置 `webdriver.chrome.driver`。
