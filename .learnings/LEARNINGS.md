# Learnings Log

## Categories
- correction: User corrections ("No, that's wrong...")
- knowledge_gap: Information user provided that I didn't know
- best_practice: Better approach discovered
- simplify_and_harden: Pattern improvement

## Format
See SKILL.md for full format template.

<!-- Add entries below -->

## [LRN-20260312-001] 分条发送规则

**Logged**: 2026-03-12T01:45:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: workflow

### Summary
推送到飞书文档时不需要分多条发送，应一次性写完

### Details
用户提醒：给飞书文档时不需分多条，写一篇完整的即可

### Suggested Action
后续推送到飞书文档时，应一次性完整写入，不要拆分多条消息

### Metadata
- Source: user_feedback
- Related Files: AGENTS.md
- Status: resolved

---

## [LRN-20260312-002] 飞书文档标题等级统一

**Logged**: 2026-03-12T02:15:00+08:00
**Priority**: high
**Status**: resolved
**Area**: feishu_doc

### Summary
飞书文档使用统一的标题等级结构：日期用## (Heading2)，文章用### (Heading3)

### Details
- 飞书不能用markdown语法改变标题等级，必须用API的block类型
- 写文档时用 # = Heading1, ## = Heading2, ### = Heading3
- 不能在已有内容上修改标题等级，必须删除重建
- 成功经验：直接用feishu_doc write重写整个文档，一次性完成

### Suggested Action
后续写飞书文档时，直接用write action一次性写入完整内容，确保格式统一

### Metadata
- Source: successful_experience
- Related Files: .learnings/ERRORS.md
- Status: resolved
