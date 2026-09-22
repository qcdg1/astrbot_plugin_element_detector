# 要素察觉 (Element Detector)

一个 AstrBot 插件：群聊消息中出现指定关键词时，立刻从该关键词的回复池里随机抽一句发出去。

所有规则都在插件页面里可视化管理——新增、编辑、删除，不需要碰 JSON。数据存在独立文件中，更新版本、修改插件信息都不会丢失。

---

## 功能特性

| 特性 | 说明 |
|---|---|
| 关键词触发 | 消息中出现关键词即触发回复 |
| 多群多关键词 | 群号和关键词都支持用 `\|` 分隔一次填多个 |
| 独立回复池 | 每个关键词对应一个回复池，随机抽一条发送 |
| 优先级 | 同群同关键词命中多条规则时，取优先级最高的那条 |
| 页面管理 | 所有规则在插件页面里增删改，无需编辑配置文件 |
| 导入导出 | 支持 JSON 一键导出备份、导入恢复 |
| 阻止 LLM | 可选，触发后不再交给 LLM 处理（默认开启） |
| 独立存储 | 规则存在独立文件中，与插件 metadata 解耦，更新版本不丢数据 |
| 纯文本匹配 | 只匹配文本内容，图片、表情、@ 不参与匹配，避免误触发 |

---

## 安装

1. 将插件目录放到 AstrBot 的 `data/plugins/` 下：
data/plugins/astrbot_plugin_element_detector/
├── main.py
├── _conf_schema.json
├── metadata.yaml
├── README.md
├── README.en.md
└── pages/
└── manager/
└── index.html

text

2. 在 AstrBot 管理面板中重载插件，或重启 AstrBot。
3. 打开插件页面，进入「规则管理」，开始添加规则。

---

## 使用方法

### 打开规则管理页面

在 AstrBot 插件管理页找到「要素察觉」，点击插件卡片进入详情页，就能看到「规则管理」页面。

### 新增一条规则

1. 点击「+ 新增规则」。
2. 填写表单：
- **规则名称**：起个便于识别的名字，如「晚安规则」
- **群号**：目标群，多个用 `|` 分隔，如 `123456789|987654321`
- **关键词**：触发词，多个用 `|` 分隔，如 `晚安|早安`
- **回复池**：每行一条，触发时随机选一条发送
- **优先级**：数值越大越高，默认 `0`
3. 点「保存」。

### 编辑 / 删除规则

在规则卡片右侧点「编辑」或「删除」即可。

### 导入 / 导出

页面顶部的 JSON 面板支持：

- **导出全部规则**：把当前所有规则输出成 JSON，可复制保存做备份
- **导入（追加）**：粘贴 JSON 后追加到现有规则
- **导入（覆盖）**：粘贴 JSON 后替换全部现有规则
- **清空全部规则**：清掉所有规则

导出的 JSON 格式示例：

```json
[
{
 "rule_name": "晚安规则",
 "group_id": "123456789",
 "keyword": "晚安|早安",
 "replies": ["晚安好梦~", "早啊", "睡个好觉"],
 "priority": 0
}
]
数据存储
所有规则保存在独立文件中，与插件元信息（版本号、作者、仓库地址等）完全解耦。

存储位置
text
<AstrBot数据目录>/plugin_data/astrbot_plugin_element_detector/rules.json
AstrBot 数据目录通常是部署目录下的 data/ 文件夹，具体取决于你的部署方式

文件是标准的 JSON 数组，可以直接查看和手动编辑

备份与迁移
操作	方法
备份	页面点「导出全部规则」，或直接拷贝 rules.json 文件
恢复	页面粘贴 JSON 点「导入（覆盖）」，或把 rules.json 放回原路径
换机器	拷贝整个 plugin_data/astrbot_plugin_element_detector/ 目录到新机器同位置
什么时候会丢数据
情况	是否丢失
重启 AstrBot	不丢
重载插件	不丢
更新插件版本	不丢
修改 metadata（版本/作者/repo）	不丢
卸载后重装插件	不丢（数据在 plugin_data 里，不在插件目录）
删除 plugin_data/astrbot_plugin_element_detector/ 目录	会丢
删除整个 AstrBot 数据目录	会丢
从旧版本迁移
如果你之前用的是早期版本（数据存在 KV 存储里），首次启动新版插件时会自动从 KV 迁移一次，把旧规则写入 rules.json。迁移完成后不再依赖 KV。

迁移过程会打印日志：

text
[要素察觉] 已从旧 KV 迁移 N 条规则到 .../rules.json
如果自动迁移没有生效（例如改 metadata 导致 KV 命名空间变了），可以手动迁移：

停掉 AstrBot

用 SQLite 工具打开数据目录下的 data_v2.db

执行：

sql
SELECT key, value FROM kv_storage WHERE key LIKE '%element_detector_rules%';
（表名可能不同，先 SELECT name FROM sqlite_master WHERE type='table'; 查看）

从 value 里复制出 JSON 数组

启动 AstrBot，进入规则管理页，粘贴到 JSON 框，点「导入（覆盖）」

匹配逻辑
情况	结果
同群同关键词有多条规则	取 priority 最高的那条
消息命中多个不同关键词	取全局 priority 最高的关键词的回复池
优先级并列	按规则在列表中的顺序，先添加的胜出
未填 priority	默认 0，最低优先级
配置项
插件配置里只保留一个开关：

配置键	类型	默认值	说明
block_llm	bool	true	触发后是否阻止 LLM 继续处理该消息
所有规则都在页面里维护，配置页不放规则字段。

更新版本的推荐流程
因为数据已经和插件元信息解耦，更新版本非常简单：

修改 main.py、index.html 等代码文件

修改 metadata.yaml 的 version、desc 等字段（不要改 name）

重载插件

规则数据会自动从 rules.json 加载，不受任何影响。

唯一需要注意的是：metadata.yaml 的 name、main.py 的 PLUGIN_NAME、DATA_DIR_NAME 这三个值必须保持一致，定下来后就别再动了。

常见问题
Q: 配置后完全没反应？

查看 AstrBot 日志中是否出现 [要素察觉] 加载完成。

确认规则是否正确保存：进入插件页面看规则卡片是否存在。

确认触发消息是群消息，且包含纯文本。

Q: 关键词命中了却有两个回复？

把 block_llm 设为 true（默认值），否则 LLM 也可能同时回复。

Q: 数据存哪里？会不会丢？

存在 <AstrBot数据目录>/plugin_data/astrbot_plugin_element_detector/rules.json。重启、重载、更新版本都不丢，只有删除该目录或整个数据目录才会丢。建议定期用页面「导出」做备份。

Q: 改 metadata 后数据没了？

现在不会了。数据存在固定路径的独立文件中，与插件元信息完全解耦。如果发现数据读不到，检查三个地方是否一致：metadata.yaml 的 name、main.py 的 PLUGIN_NAME、DATA_DIR_NAME。

Q: 想让同一关键词在不同群用不同回复池怎么办？

建两条规则，group_id 分别填不同的群号即可。

Q: 支持哪些平台？

插件本身平台无关，AstrBot 支持的平台都能用。只要消息里包含纯文本关键词就能触发。

许可
MIT License。