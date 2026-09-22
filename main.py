import random
from sys import maxsize
from typing import Dict, List, Optional, Tuple

import astrbot.api.message_components as Comp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.web import error_response, json_response, request
from astrbot.api import logger

KV_KEY_RULES = "element_detector_rules"
PLUGIN_NAME = "astrbot_plugin_element_detector"


@register(
    PLUGIN_NAME,
    "your_name",
    "要素察觉：群聊中出现关键词时立刻随机回复。规则全部在插件页面里维护。",
    "7.0.0",
    "https://github.com/your_name/astrbot_plugin_element_detector",
)
class ElementDetectorPlugin(Star):
    def __init__(self, context: Context, config: dict | None = None):
        super().__init__(context)
        self.config = config or {}

        self.block_llm: bool = self.config.get("block_llm", True)

        # 全部规则都存在这里（KV 持久化）
        self.rules: List[dict] = []
        self._kv_loaded = False

        # group_id -> {keyword: [(priority, [replies]), ...]}
        self.rules_by_group: Dict[str, Dict[str, List[Tuple[int, List[str]]]]] = {}

        # 注册 Web API
        api_base = f"/{PLUGIN_NAME}"
        logger.info(f"[要素察觉] 准备注册 Web API，前缀: {api_base}")

        context.register_web_api(f"{api_base}/list_rules",     self.api_list_rules,     ["GET"],  "列出全部规则")
        context.register_web_api(f"{api_base}/add_rule",       self.api_add_rule,       ["POST"], "新增规则")
        context.register_web_api(f"{api_base}/update_rule",    self.api_update_rule,    ["POST"], "更新规则")
        context.register_web_api(f"{api_base}/delete_rule",    self.api_delete_rule,    ["POST"], "删除规则")
        context.register_web_api(f"{api_base}/import_rules",   self.api_import_rules,   ["POST"], "批量导入规则")
        context.register_web_api(f"{api_base}/export_rules",   self.api_export_rules,   ["GET"],  "导出全部规则")
        context.register_web_api(f"{api_base}/clear_rules",    self.api_clear_rules,    ["POST"], "清空全部规则")

        logger.info("[要素察觉] Web API 注册完成")
        logger.info(
            f"[要素察觉] 加载完成 | 阻止LLM={'是' if self.block_llm else '否'} | "
            f"规则将在首次消息或页面访问时从 KV 加载"
        )

    # ------------------------------------------------------------------
    # KV
    # ------------------------------------------------------------------
    async def _ensure_kv_loaded(self):
        if self._kv_loaded:
            return
        self._kv_loaded = True
        try:
            data = await self.get_kv_data(KV_KEY_RULES, [])
            if isinstance(data, list):
                self.rules = data
                self._rebuild_rules()
                logger.info(f"[要素察觉] 从 KV 加载了 {len(self.rules)} 条规则")
        except Exception as e:
            logger.error(f"[要素察觉] KV 加载失败: {e}")

    async def _save_rules(self):
        try:
            await self.put_kv_data(KV_KEY_RULES, self.rules)
        except Exception as e:
            logger.error(f"[要素察觉] KV 保存失败: {e}")

    # ------------------------------------------------------------------
    # 规则
    # ------------------------------------------------------------------
    @staticmethod
    def _split_multi(value) -> List[str]:
        if value is None:
            return []
        return [p.strip() for p in str(value).split("|") if p.strip()]

    def _normalize_rule(self, rule: dict) -> Optional[dict]:
        """规范化一条规则，字段非法则返回 None。"""
        if not isinstance(rule, dict):
            return None
        gids = self._split_multi(rule.get("group_id", ""))
        kws = self._split_multi(rule.get("keyword", ""))
        replies_raw = rule.get("replies", [])
        replies = (
            [str(r).strip() for r in replies_raw if str(r).strip()]
            if isinstance(replies_raw, list)
            else []
        )
        try:
            priority = int(rule.get("priority", 0))
        except (TypeError, ValueError):
            priority = 0
        if not gids or not kws or not replies:
            return None
        return {
            "rule_name": str(rule.get("rule_name", "")).strip(),
            "group_id": str(rule.get("group_id", "")).strip(),
            "keyword": str(rule.get("keyword", "")).strip(),
            "replies": replies,
            "priority": priority,
        }

    def _rebuild_rules(self):
        self.rules_by_group = {}
        for idx, rule in enumerate(self.rules):
            norm = self._normalize_rule(rule)
            if not norm:
                logger.warning(f"[要素察觉] 第 {idx} 条规则字段缺失，跳过")
                continue
            for gid in self._split_multi(norm["group_id"]):
                kw_map = self.rules_by_group.setdefault(gid, {})
                for kw in self._split_multi(norm["keyword"]):
                    kw_map.setdefault(kw, []).append((norm["priority"], norm["replies"]))

    # ------------------------------------------------------------------
    # 消息处理
    # ------------------------------------------------------------------
    @staticmethod
    def _get_text(event: AstrMessageEvent) -> str:
        parts = []
        for seg in event.get_messages():
            if isinstance(seg, Comp.Plain):
                parts.append(seg.text)
        return "".join(parts)

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE, priority=maxsize)
    async def on_group_message(self, event: AstrMessageEvent):
        await self._ensure_kv_loaded()

        group_id = str(event.get_group_id())
        kw_map = self.rules_by_group.get(group_id)
        if not kw_map:
            return

        text = self._get_text(event)
        if not text:
            return

        best_priority: Optional[int] = None
        best_replies: Optional[List[str]] = None
        best_kw = ""
        for kw, entries in kw_map.items():
            if kw not in text:
                continue
            prio, replies = max(entries, key=lambda e: e[0])
            if best_priority is None or prio > best_priority:
                best_priority = prio
                best_replies = replies
                best_kw = kw

        if not best_replies:
            return

        reply = random.choice(best_replies)
        logger.info(f"[要素察觉] 群{group_id} 命中 '{best_kw}' (优先级{best_priority}) → {reply}")
        yield event.plain_result(reply)
        if self.block_llm:
            event.should_call_llm(False)
            event.stop_event()

    # ------------------------------------------------------------------
    # Web API
    # ------------------------------------------------------------------
    async def api_list_rules(self):
        await self._ensure_kv_loaded()
        return json_response({"rules": [dict(r) for r in self.rules]})

    async def api_add_rule(self):
        await self._ensure_kv_loaded()
        payload = await request.json(default={})
        norm = self._normalize_rule(payload.get("rule", {}))
        if not norm:
            return error_response("规则字段不完整（需要群号、关键词、至少一条回复）")
        self.rules.append(norm)
        await self._save_rules()
        self._rebuild_rules()
        return json_response({"ok": True, "index": len(self.rules) - 1})

    async def api_update_rule(self):
        await self._ensure_kv_loaded()
        payload = await request.json(default={})
        try:
            index = int(payload.get("index", -1))
        except (TypeError, ValueError):
            return error_response("index 无效")
        if index < 0 or index >= len(self.rules):
            return error_response("规则索引越界")
        norm = self._normalize_rule(payload.get("rule", {}))
        if not norm:
            return error_response("规则字段不完整")
        self.rules[index] = norm
        await self._save_rules()
        self._rebuild_rules()
        return json_response({"ok": True})

    async def api_delete_rule(self):
        await self._ensure_kv_loaded()
        payload = await request.json(default={})
        try:
            index = int(payload.get("index", -1))
        except (TypeError, ValueError):
            return error_response("index 无效")
        if index < 0 or index >= len(self.rules):
            return error_response("规则索引越界")
        self.rules.pop(index)
        await self._save_rules()
        self._rebuild_rules()
        return json_response({"ok": True})

    async def api_import_rules(self):
        await self._ensure_kv_loaded()
        payload = await request.json(default={})
        rules = payload.get("rules", [])
        mode = payload.get("mode", "append")   # append | replace
        if not isinstance(rules, list):
            return error_response("rules 必须是数组")

        if mode == "replace":
            self.rules = []

        added = 0
        for item in rules:
            norm = self._normalize_rule(item)
            if not norm:
                continue
            self.rules.append(norm)
            added += 1

        await self._save_rules()
        self._rebuild_rules()
        return json_response({"imported": added, "total": len(self.rules)})

    async def api_export_rules(self):
        await self._ensure_kv_loaded()
        return json_response({"rules": [dict(r) for r in self.rules]})

    async def api_clear_rules(self):
        await self._ensure_kv_loaded()
        count = len(self.rules)
        self.rules = []
        await self._save_rules()
        self._rebuild_rules()
        return json_response({"cleared": count})

    async def terminate(self):
        logger.info("[要素察觉] 插件已卸载")