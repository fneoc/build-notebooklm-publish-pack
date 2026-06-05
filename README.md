# build-notebooklm-publish-pack

把任意可验证的网络内容，变成可直接发布的中文/英文自媒体内容包。

这不是一个“摘要工具”，而是一套内容生产到发布的完整工作流。它把一篇文章、一份报告、一个网页、一段笔记，整理成可运营、可复用、可持续发布的素材系统，帮助你把一次输入变成多平台输出。

## 项目亮点

- 面向 NotebookLM 的源内容预检与长文策略判断
- 自动创建干净 NotebookLM 笔记本、上传 PDF/companion、触发视频和图片生成
- 中文 / 英文双语发布包生成
- 适配视频号、BILIBILI、TikTok、YouTube Shorts、小红书、LinkedIn 的平台文案
- 7 天复用日历与运营检查单
- 比例遮罩图与发布包审计，减少“能生成但不能发”的尴尬
- 适合科技资讯、行业报告、研究文章、长文专栏、PDF 和网页内容

## 它适合什么

- 科技资讯、行业报告、研究文章、长文专栏
- PDF、HTML 网页、Markdown、纯文本、社媒帖、视频页、可抓取的网络内容
- 需要同时产出中文和英文内容的账号
- 想把“单次内容生产”升级成“可持续运营”的自媒体工作流

## 它能做什么

- 识别来源类型，判断内容是新闻、报告、教程、案例、观点还是普通文章
- 预检网页和文件，判断是否适合 NotebookLM、是否需要源派生 companion
- 生成 NotebookLM 的中文/英文提示词和 briefing companion
- 通过浏览器自动化上传来源到干净 NotebookLM 笔记本，校验来源数量，轮询并下载官方视频/信息图
- 生成平台发布草稿、7 天复用日历和运营检查单
- 生成比例遮罩图，帮助短视频和信息流封面适配不同平台
- 审计最终发布包，发现坏媒体、漏文件、命名错误和来源污染

## 产出是什么

一个完整发布包通常会包含：

- `source-manifest.json`
- `source-preflight.txt`
- `briefing-companion-zh.md`
- `briefing-companion-en.md`
- `notebooklm-prompt-zh.txt`
- `notebooklm-prompt-en.txt`
- `notebooklm-downloads-manifest.json`
- `notebooklm-automation-log.json`
- `content-plan.json`
- `publish-ops-checklist.md`
- `repurposing-calendar.md`
- `video-zh-notebooklm.mp4`
- `video-en-notebooklm.mp4`
- `infographic-horizontal.png`
- `infographic-vertical.png`
- `publish-wechat-video.txt`
- `publish-bilibili.txt`
- `publish-tiktok-en.txt`
- `publish-linkedin.txt`

## 工作流

1. 先用 `prepare_source.py` 做预检，判断内容类型、正文长度、图片数和长文模式。
2. 再用 `draft_pack_plan.py` 生成 briefing companion、NotebookLM prompt、运营日历和平台草稿。
3. 用浏览器自动化驱动 NotebookLM：创建干净笔记本、上传来源、触发视频/信息图、等待生成、下载官方资产。
4. 用 `audit_publish_pack.py` 做最终审计，确认文件齐全、媒体可读、来源不污染。

## 为什么它有用

很多内容工具只能帮你“说完一篇内容”，但不能帮你“持续运营一个账号”。这个技能的目标是把内容生产拆成可重复的块：源内容预检、角度选择、双语发布、平台适配、复用排期和最终校验。

换句话说，它更像一个自媒体运营引擎，而不是一个一次性的摘要器。

## 适合收藏的原因

- 你不需要每次都从零搭流程
- 你可以先预检，再决定要不要进 NotebookLM
- 你能得到可审计、可复用、可继续迭代的发布包
- 你可以把单次爆发变成稳定更新的内容管线

## 快速开始

```bash
scripts/prepare_source.py "<url-or-file>" --output-dir "<package-folder>" --base "<base>"
scripts/draft_pack_plan.py "<package-folder>/<base>-source-manifest.json" --output-dir "<package-folder>" --base "<base>"
scripts/audit_publish_pack.py "<package-folder>" --strict
```

如果你在评估一个陌生网站，先加 `--dry-run` 看预检结果，再决定是不是进入 NotebookLM。
如果要生成官方 NotebookLM 视频和图片，请使用已登录 Google 账号的 Chrome；技能会优先自动上传和下载，只有遇到登录、验证码、文件选择器或生成超时等真实阻塞时才转为人工交接。

## 示例提示

- “把这篇文章做成适合视频号、BILIBILI 和 TikTok 的中英双语发布包。”
- “这个网页内容先帮我预检，判断适合做新闻、报告还是教程。”
- “继续这个包，检查现有文件，补齐缺失的发布文案和媒体资产。”
- “NotebookLM 已经生成英文视频了，帮我整理成完整发布包。”

## 设计原则

- 优先基于真实来源，不靠猜
- 优先做可运营内容，不只做总结
- 优先保留中文和英文两个受众的差异
- 优先让最终产物可以检查、可以复用、可以持续发布
