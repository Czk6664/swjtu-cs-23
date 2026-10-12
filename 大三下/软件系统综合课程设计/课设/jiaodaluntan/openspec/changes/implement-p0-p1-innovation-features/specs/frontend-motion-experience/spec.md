## ADDED Requirements

### Requirement: 前端动效使用 Anime.js 实现
系统 SHALL 使用 Anime.js 为首页和关键交互提供流畅动效，并通过前端构建系统打包该依赖。

#### Scenario: 构建前端产物
- **WHEN** 执行前端构建
- **THEN** Anime.js 被打包进前端产物，页面运行时不依赖 CDN 或外部本地路径

### Requirement: 页面动效保持流畅不卡顿
系统 MUST 优先使用 transform 和 opacity 等低成本动画属性，避免造成明显卡顿。

#### Scenario: 首页加载动画
- **WHEN** 用户打开首页
- **THEN** 帖子卡片、热榜区域和热点词云以平滑入场动画出现，不阻塞内容阅读

### Requirement: 动效尊重减少动态效果偏好
系统 SHALL 在用户或浏览器偏好减少动态效果时降低或关闭非必要动画。

#### Scenario: 用户减少动态效果
- **WHEN** 浏览器匹配 `prefers-reduced-motion: reduce`
- **THEN** 系统不播放大幅度位移动画，保留静态可读内容

### Requirement: 动画实例需要可清理
系统 MUST 避免页面重复渲染后产生重复动画、重复定时器或内存泄漏。

#### Scenario: 页面重新渲染
- **WHEN** 用户从首页跳转到其他页面后再返回首页
- **THEN** 系统重新初始化必要动画，并清理旧动画实例或旧计时器
