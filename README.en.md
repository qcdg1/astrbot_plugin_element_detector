---

## 📄 `README.en.md`（英文）

```markdown
# Element Detector

An AstrBot plugin: when a group message contains a configured keyword, the bot instantly replies with a random line from that keyword's reply pool.

All rules are managed through the plugin's own page — create, edit, delete without touching JSON. Data is stored in a standalone file, so updating the plugin or editing metadata won't lose anything.

---

## Features

| Feature | Description |
|---|---|
| Keyword trigger | Replies as soon as the keyword appears in a message |
| Multi-group & multi-keyword | Both fields accept `\|`-separated lists |
| Independent reply pools | Each keyword maps to its own pool; one line is picked at random |
| Priority | When multiple rules match, the highest priority one is used |
| Page management | Add, edit, and delete rules directly on the plugin page |
| Import / Export | One-click JSON export and import |
| Block LLM | Optionally stop the LLM from handling the matched message (on by default) |
| Standalone storage | Rules live in their own file, decoupled from plugin metadata |
| Plain-text only | Only text segments are matched; images and mentions are ignored |

---

## Installation

1. Place the plugin folder into AstrBot's `data/plugins/` directory:
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

2. Reload the plugin in the AstrBot dashboard, or restart AstrBot.
3. Open the plugin page and enter "Rule Manager" to start adding rules.

---

## Usage

### Open the Rule Manager

In the AstrBot plugin dashboard, click the "Element Detector" card. You'll see a "Rule Manager" page.

### Add a rule

1. Click "+ New Rule".
2. Fill in:
- **Rule name**: a label for your own reference, e.g. "Good Night"
- **Group IDs**: target groups, `|`-separated, e.g. `123456789|987654321`
- **Keywords**: triggers, `|`-separated, e.g. `good night|good morning`
- **Replies**: one per line; one is picked at random when triggered
- **Priority**: higher wins, default `0`
3. Click "Save".

### Edit / Delete a rule

Use the buttons on each rule card.

### Import / Export

The JSON panel at the top supports:

- **Export all rules**: outputs all rules as JSON for backup
- **Import (append)**: appends pasted JSON rules to existing ones
- **Import (replace)**: replaces all existing rules with pasted JSON
- **Clear all rules**: removes everything

Example exported JSON:

```json
[
{
 "rule_name": "Good Night",
 "group_id": "123456789",
 "keyword": "good night|good morning",
 "replies": ["sweet dreams~", "morning", "sleep well"],
 "priority": 0
}
]
Data Storage
All rules are stored in a standalone file, completely decoupled from plugin metadata (version, author, repository, etc.).

Location
text
<AstrBot data dir>/plugin_data/astrbot_plugin_element_detector/rules.json
The AstrBot data directory is usually a data/ folder under the deployment directory

The file is a plain JSON array — you can view or edit it directly

Backup & Migration
Action	Method
Backup	Click "Export all rules" on the page, or copy rules.json directly
Restore	Paste JSON and click "Import (replace)", or put rules.json back
Move to another machine	Copy the entire plugin_data/astrbot_plugin_element_detector/ directory
When data is lost
Situation	Lost?
Restart AstrBot	No
Reload plugin	No
Update plugin version	No
Edit metadata (version/author/repo)	No
Uninstall & reinstall plugin	No (data lives in plugin_data, not the plugin folder)
Delete plugin_data/astrbot_plugin_element_detector/	Yes
Delete the entire AstrBot data directory	Yes
Migrating from an Older Version
If you used an earlier version (data stored in KV), the new plugin will automatically migrate from KV once on first start, writing the old rules into rules.json. After migration, KV is no longer used.

Migration prints a log line:

text
[要素察觉] 已从旧 KV 迁移 N 条规则到 .../rules.json
If automatic migration didn't work (e.g. metadata edits changed the KV namespace), you can migrate manually:

Stop AstrBot

Open data_v2.db in the data directory with an SQLite tool

Run:

sql
SELECT key, value FROM kv_storage WHERE key LIKE '%element_detector_rules%';
(Table name may differ; check with SELECT name FROM sqlite_master WHERE type='table';)

Copy the JSON array from value

Start AstrBot, go to the Rule Manager page, paste it, click "Import (replace)"

Matching Logic
Situation	Outcome
Multiple rules match the same keyword in a group	Highest priority wins
One message matches multiple different keywords	The keyword with the highest global priority wins
Equal priorities	First added rule wins
priority omitted	Defaults to 0 (lowest)
Configuration
Only one option remains in the plugin config page:

Key	Type	Default	Description
block_llm	bool	true	Whether to block the LLM after the plugin replies
All rules are managed on the plugin page, not in the config file.

Recommended Update Workflow
Since data is decoupled from plugin metadata, updating the plugin is simple:

Edit main.py, index.html, etc.

Edit metadata.yaml fields like version, desc (do not change name)

Reload the plugin

Rules are automatically loaded from rules.json and remain unaffected.

The only thing to watch: metadata.yaml's name, main.py's PLUGIN_NAME, and DATA_DIR_NAME must stay consistent. Set them once and don't touch them again.

FAQ
Q: Nothing happens after configuration.

Check the log for [要素察觉] 加载完成.

Verify rules exist on the plugin page.

Make sure the message is a group message and contains plain text.

Q: The keyword matched but there are two replies.

Set block_llm to true (default), otherwise the LLM may also reply.

Q: Where is the data stored? Will it be lost?

In <AstrBot data dir>/plugin_data/astrbot_plugin_element_detector/rules.json. Restarting, reloading, and updating versions won't lose it. Only deleting that directory or the whole data directory will. Use "Export" regularly for backups.

Q: I lost data after editing metadata.

Not anymore. Data lives in a standalone file at a fixed path, fully decoupled from plugin metadata. If rules appear to be missing, check that metadata.yaml's name, main.py's PLUGIN_NAME, and DATA_DIR_NAME are consistent.

Q: Different reply pools for the same keyword across groups.

Create one rule per group with different group_id.

Q: Which platforms are supported?

The plugin is platform-agnostic. Any platform AstrBot supports will work, as long as the message contains plain-text keywords.

License
MIT License.