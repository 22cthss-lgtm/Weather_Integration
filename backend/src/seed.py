from .models.faq_repository import create_faq, ensure_category, list_faqs


def seed_faqs() -> None:
    if list_faqs():
        return

    for name in ["系統使用", "觀測資料", "颱風資訊"]:
        ensure_category(name)

    create_faq(
        category="系統使用",
        title="如何查看最新彩色衛星雲圖？",
        summary="說明首頁卡片與單圖頁的查看方式。",
        content=(
            "# 如何查看最新彩色衛星雲圖？\n\n"
            "你可以在首頁 Dashboard 看到最新卡片，或點進對應影像頁查看大圖。\n\n"
            "## 建議流程\n\n"
            "- 先在首頁確認最新更新時間\n"
            "- 再點進詳細頁查看原始來源連結\n"
        ),
        tags=["衛星", "首頁"],
        is_pinned=True,
    )

    create_faq(
        category="觀測資料",
        title="雷達回波圖多久更新一次？",
        summary="說明本地展示頁與資料來源更新節奏的關係。",
        content=(
            "# 雷達回波圖多久更新一次？\n\n"
            "頁面會顯示目前抓取到的最新雷達回波圖，實際更新頻率仍以來源站資料發布為主。"
        ),
        tags=["雷達", "更新頻率"],
        is_pinned=False,
    )
