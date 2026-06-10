from __future__ import annotations

from app.models.schemas import PlatformRule


def all_platform_rules() -> list[PlatformRule]:
    return [
        platform_rule("xiaohongshu"),
        platform_rule("pdd"),
        platform_rule("taobao"),
        platform_rule("tmall"),
        platform_rule("douyin"),
        platform_rule("jd"),
        platform_rule("independent"),
    ]


def platform_rule(platform: str) -> PlatformRule:
    key = (platform or "taobao").lower().strip()
    if key in {"xiaohongshu", "xhs", "red"}:
        return PlatformRule(
            platform="xiaohongshu",
            merchantType="content_commerce",
            displayName="小红书电商",
            objective="种草笔记式真实体验，强调场景、细节和适合人群",
            voice="第一人称、轻分享、生活方式表达，避免强促销口吻",
            structure=["使用背景", "具体体验细节", "适合人群", "克制推荐理由"],
            positiveSignals=["生活场景", "细节观察", "主观感受边界", "适合/不适合人群"],
            avoidClaims=["硬广式促销", "绝对化种草", "无依据前后对比", "伪装普通用户身份"],
            riskTerms=["闭眼入", "必买", "全网最", "冲就完了", "亲测有效"],
            maxShortRunes=120,
            requireExperienceEvidence=True,
            merchantVoiceReviewRisk=True,
        )
    if key in {"pdd", "pinduoduo"}:
        return PlatformRule(
            platform="pdd",
            merchantType="price_value_ecommerce",
            displayName="拼多多电商",
            objective="突出到手体验、性价比、规格清楚和售后确定性",
            voice="短句、直接、接地气，少修饰，重点讲值不值",
            structure=["到手检查", "价格/规格感知", "物流包装", "复购或家庭使用场景"],
            positiveSignals=["到手状态", "规格明确", "包装物流", "性价比表述有边界"],
            avoidClaims=["全网最低", "夸大补贴", "虚构低价对比", "无依据售后承诺"],
            riskTerms=["全网最低", "最低价", "假一赔十", "秒杀全平台"],
            maxShortRunes=90,
        )
    if key in {"douyin", "tiktok"}:
        return PlatformRule(
            platform="douyin",
            merchantType="short_video_live_commerce",
            displayName="抖音电商",
            objective="适配短视频/直播讲解，开头有抓手，内容节奏短而可信",
            voice="短句、口播感、先说结论，再给可见细节",
            structure=["一句结论", "3 个可见细节", "使用场景", "理性下单提醒"],
            positiveSignals=["开头抓手", "可视化细节", "口播节奏", "理性提醒"],
            avoidClaims=["制造紧迫焦虑", "直播间最低价", "夸大效果", "倒计时式诱导"],
            riskTerms=["最后一波", "错过再等一年", "直播间最低价", "保证有效"],
            maxShortRunes=80,
            requireExperienceEvidence=True,
            merchantVoiceReviewRisk=True,
        )
    if key in {"jd", "jingdong"}:
        return PlatformRule(
            platform="jd",
            merchantType="rational_ecommerce",
            displayName="京东电商",
            objective="偏理性决策，强调参数、配送、售后和稳定体验",
            voice="清楚、克制、参数导向，少情绪化表达",
            structure=["核心参数", "使用表现", "配送/包装", "售后或长期使用"],
            positiveSignals=["参数清晰", "配送体验", "售后边界", "稳定性"],
            avoidClaims=["无依据正品承诺", "夸大官方背书", "未经确认的保修承诺"],
            riskTerms=["官方唯一", "永久保修", "绝对正品"],
            maxShortRunes=100,
        )
    if key in {"independent", "shopify", "dtc"}:
        return PlatformRule(
            platform="independent",
            merchantType="brand_dtc",
            displayName="独立站/DTC",
            objective="突出品牌语气、信任背书和真实使用场景",
            voice="品牌友好、清晰、有信任感，避免平台黑话",
            structure=["品牌价值", "产品细节", "使用场景", "服务边界"],
            positiveSignals=["品牌一致性", "信任感", "服务信息", "场景化推荐"],
            avoidClaims=["平台促销黑话", "虚构权威背书", "未经证实的全球销量"],
            riskTerms=["全球第一", "权威认证", "唯一指定"],
            maxShortRunes=110,
        )
    return _marketplace_rule("tmall" if key == "tmall" else "taobao", "天猫" if key == "tmall" else "淘宝")


def _marketplace_rule(platform: str, label: str) -> PlatformRule:
    return PlatformRule(
        platform=platform,
        merchantType="marketplace_ecommerce",
        displayName=f"{label}电商",
        objective="货架电商好评草稿，强调商品属性、真实体验和服务细节",
        voice="自然、平实、有商品细节，适合货架电商评价区",
        structure=["购买/使用场景", "商品属性", "体验细节", "物流/客服/售后"],
        positiveSignals=["SKU/规格", "真实使用细节", "物流包装", "客服售后边界"],
        avoidClaims=["刷评口吻", "无依据效果承诺", "绝对化排名", "虚构订单或回购"],
        riskTerms=["全网第一", "旗舰店唯一", "效果立竿见影", "永久有效"],
        maxShortRunes=105,
    )

