edge_cases = [

    # 模糊趋势
    {
        "text": "最近几年销量好像越来越好了。",
        "label": "trend"
    },

    {
        "text": "用户数量感觉比以前高不少。",
        "label": "comparison"
    },

    # 无明确数字
    {
        "text": "公司收入主要来自软件业务。",
        "label": "composition"
    },

    {
        "text": "学生成绩大多数处于中等水平。",
        "label": "distribution"
    },

    # 多意图混合
    {
        "text": "2020到2023年销量持续增长，其中A产品销量始终高于B产品。",
        "label": "trend"
    },

    {
        "text": "广告投入增加后销量提升明显。",
        "label": "correlation"
    },

    # 口语化
    {
        "text": "这几年业绩一路往上涨。",
        "label": "trend"
    },

    {
        "text": "线上卖得比线下好多了。",
        "label": "comparison"
    },

    # 缺失数据
    {
        "text": "研发费用占整体支出比例最大。",
        "label": "composition"
    },

    {
        "text": "访问用户基本都集中在年轻人。",
        "label": "distribution"
    }
]