"""
题库查询工具
通过 MySQL 查询 question_library 表，支持维度筛选和随机出题
"""
from typing import Any

from common.mysql_util import execute_query

# 维度白名单（SQL 注入防护）
DIMENSION_WHITELIST = {
    "question_type": {"知识", "话术", "情景应对", "产品推荐", "不限"},
    "sales_stage": {"迎宾", "需求挖掘", "推荐", "异议处理", "成交", "售后", "不限"},
    "customer_type": {"新手", "送礼", "宴请", "收藏", "团购", "不限"},
    "product_category": {"产区", "品种", "年份", "配餐", "储存", "不限"},
    "country": {
        "法国", "意大利", "西班牙", "德国", "葡萄牙", "美国", "智利", "阿根廷",
        "澳大利亚", "新西兰", "南非", "中国", "奥地利", "希腊", "格鲁吉亚",
        "匈牙利", "罗马尼亚", "摩尔多瓦", "乌拉圭", "巴西", "不限",
    },
}


def _safe_dim(name: str, value: str) -> str:
    """维度值白名单校验，不在名单内返回 '不限'"""
    return value if value in DIMENSION_WHITELIST.get(name, set()) else "不限"


def _row_to_question(row: dict[str, Any]) -> dict[str, Any]:
    """把"数据库列名"和"对外业务字段名"解耦"""
    return {
        "id": row["question_id"],
        "question": row["question_title"],
        "answer": row["answer"],
        "question_type": row["question_type"],
        "sales_stage": row["sales_stage"],
        "customer_type": row["customer_type"],
        "product_category": row["product_category"],
        "country": row.get("country", "不限"),
    }


def _build_where(
    question_type: str,
    sales_stage: str,
    customer_type: str,
    product_category: str,
    country: str,
    exclude_ids: list[int] | None,
    keywords: list[str] | None = None,
) -> str:
    """拼 WHERE 子句，返回 where_sql"""
    where_clauses = []
    for col, val in [
        ("question_type", _safe_dim("question_type", question_type)),
        ("sales_stage", _safe_dim("sales_stage", sales_stage)),
        ("customer_type", _safe_dim("customer_type", customer_type)),
        ("product_category", _safe_dim("product_category", product_category)),
        ("country", _safe_dim("country", country)),
    ]:
        if val != "不限":
            where_clauses.append(f"{col}='{val}'")

    if keywords:
        safe_kw = [k.replace("'", "''") for k in keywords if k.strip()]
        if safe_kw:
            kw_conditions = " or ".join(
                # 注意：% 是 pymysql 的占位符，字面量通配符必须写成 %%（execute_query 用 sql % () 格式化）
                f"question_title like '%%{k}%%' or answer like '%%{k}%%'"
                for k in safe_kw
            )
            where_clauses.append(f"({kw_conditions})")

    if exclude_ids:
        ids = ",".join(str(i) for i in exclude_ids)
        where_clauses.append(f"question_id not in ({ids})")

    return " where " + " and ".join(where_clauses) if where_clauses else ""


def query_question(
    question_type: str = "不限",
    sales_stage: str = "不限",
    customer_type: str = "不限",
    product_category: str = "不限",
    country: str = "不限",
    exclude_ids: list[int] | None = None,
    keywords: list[str] | None = None,
) -> dict[str, Any]:
    """
    从题库按维度 + 关键词随机查询一道题（三级兜底：维度+关键词 → 纯维度 → 不限维度）

    Returns:
        {"found": True, "question": {...}} 或 {"found": False, "reason": "..."}
    """
    # 第一级：维度 + 关键词模糊匹配
    if keywords:
        where_sql = _build_where(
            question_type, sales_stage, customer_type, product_category, country,
            exclude_ids, keywords,
        )
        sql = f"SELECT * FROM question_library{where_sql} ORDER BY RAND() DESC LIMIT 1"
        rows = execute_query(sql)
        if rows:
            return {"found": True, "question": _row_to_question(rows[0])}

    # 第二级：纯维度匹配（关键词无结果时兜底）
    where_sql = _build_where(
        question_type, sales_stage, customer_type, product_category, country,
        exclude_ids,
    )
    sql = f"SELECT * FROM question_library{where_sql} ORDER BY RAND() DESC LIMIT 1"
    rows = execute_query(sql)
    if rows:
        return {"found": True, "question": _row_to_question(rows[0])}

    # 第三级：完全不限维度（极端兜底，保证有题出）
    no_dim_where = ""
    if exclude_ids:
        ids = ",".join(str(i) for i in exclude_ids)
        no_dim_where = f" where question_id not in ({ids})"
    sql = f"SELECT * FROM question_library{no_dim_where} ORDER BY RAND() DESC LIMIT 1"
    rows = execute_query(sql)
    if rows:
        return {"found": True, "question": _row_to_question(rows[0])}

    return {"found": False, "reason": "题库暂无可用题目"}
