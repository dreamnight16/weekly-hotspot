# 故障排除指南

## 抓取失败（没有数据）

**现象：** Phase 0 输出 "抓取全失败"。

**原因：**
- 微博/知乎/HN 的反爬机制触发了
- 网络不通或代理问题
- `chinese-scraper-utils` 版本过旧

**解决：**
1. 检查网络连接：`python -c "from chinese_scraper_utils import scrape_weibo_hot; print(scrape_weibo_hot()[:3])"`
2. 如果只是偶尔失败，缓存会自动回退上次的数据
3. 如果持续失败，更新依赖：`pip install --upgrade chinese-scraper-utils`

---

## DeepSeek API 错误

**现象：** Phase 1-4 重试多次后仍失败。

**常见 API 错误：**
- `401` — API Key 过期或无效，重新生成
- `429` — 请求频率过高，降低 `max_events` 或等待
- `500` — DeepSeek 服务端故障，稍后重试
- `ConnectionError` — 网络不通或代理问题

**检查 API Key：**
```bash
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/v1/models
```

---

## 博客推送失败

**现象：** GitHub Actions 每周工作流在 Push 步骤失败。

**原因：**
- `BLOG_PAT` 过期（Personal Access Token）
- Blog-mizuki 仓库的写入权限未授予
- 分支冲突

**解决：**
1. 重新生成 PAT：Settings → Developer settings → Tokens (classic) → 勾选 `repo` scope
2. 更新 GitHub Secrets 中的 `BLOG_PAT`
3. 检查 PAT 是否对 `sixtdreanight/Blog-mizuki` 仓库有效

---

## 输出文件未生成

**现象：** 流水线运行成功但 JSON/Markdown 没有出现在预期位置。

**原因：**
- `BLOG_CONTENT_DIR` 路径配置错误
- 路径在用户目录之外的路径安全校验被触发
- 磁盘空间不足
- 目录权限不足

**检查路径：**
```bash
python -c "from config import BLOG_CONTENT_DIR; print(BLOG_CONTENT_DIR)"
```

如果手动设置了 `BLOG_CONTENT_DIR`，确保它在用户主目录下（`config.py` 的安全校验）。

---

## LLM 输出校验（已自动化处理）

以下问题 **v0.3+ 已由 sanitization 层自动处理**，不再导致流水线崩溃。日志中会出现 `[sanitize]` 前缀的 WARNING 提示清洗动作：

| 问题 | 自动处理方式 |
|------|-------------|
| Edge 引用不存在的 timeline/evidence ID | 丢弃无效 edge，保留有效 edge |
| Timeline evidenceRefs 引用不存在的证据 | 从 evidenceRefs 中移除无效引用 |
| Synthesis 引用不存在的事件 ID | 从引用列表中移除无效 ID |
| 枚举值填错（如 direction 填了 currentState 的值） | 模糊匹配修正，匹配不到则用默认值 |
| 枚举值拼接（如 "对抗激化，隐性积累"） | 子串匹配第一个有效枚举值 |
| 评分超出 1-5 范围 | 自动 clamp 到合法范围 |
| Timeline 节点缺少 time 字段 | 自动填充 "未知" |
| classAnalysis 子字段缺失 | 自动填充空字符串 |
| dialecticalSummary 非字符串 | 自动转换为字符串 |

**如果 sanitization 后仍有问题：**
1. 查看 GitHub Actions 日志中 `[sanitize]` 或 `[schema]` 前缀的 WARNING/ERROR
2. 检查对应事件的 JSON 输出，确认 `timeline`、`evidence`、`edges` 中的 ID 完全一致
3. 如果大量事件被 sanitize，考虑检查 DeepSeek 模型是否降级

---

## 运行测试

### 仅单元测试（无需 API Key）
```bash
cd weekly-cli
pytest -v -m "unit"
```

### 单元测试 + 覆盖率
```bash
pytest -v -m "unit" --cov=. --cov-report=term-missing --cov-fail-under=80
```

### 全部测试（需要 API Key）
```bash
DEEPSEEK_API_KEY=sk-your-key pytest -v
```

### 测试没通过？
1. 确保 `pytest>=8.0` 和 `pytest-cov>=5.0` 已安装
2. 确保 `conftest.py` 中的 fixture 没有被修改
3. 集成测试需要合法的 `DEEPSEEK_API_KEY`，未设置时会自动跳过

---

## 覆盖率低于 80%

```bash
pytest -v -m "unit" --cov=. --cov-report=term-missing
```

重点关注 `Missing` 列中覆盖率最低的文件：
- `main.py` 的流水线编排逻辑依赖真实 API（较难在单元测试中覆盖）
- `search.py` 的 `search_event` 需要模拟 DDG/Bing API
- `config.py` 的 `sys.exit` 分支在测试中无法正常触发

目前 80% 的最小阈值是通过 mix of unit tests + mock tests 达到的。
