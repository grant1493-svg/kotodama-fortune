"""
うけとめ相談室 — 記事・投稿設定
ジャンルごとに1エントリ。note_url は公開後にユーザーが埋める。
generate_thumbnail.py と x_post.py の両方がここを参照する。
"""

ARTICLES = {
    "love": {
        "genre_label": "恋愛の悩み",
        "thumbnail_title": "なぜ恋愛は苦しいのか",
        "article_path": r"C:\Users\admin\Documents\Codex\2026-08-07\note-worry-method\note_love_worry_article_1.md",
        "note_url": "https://note.com/soudan_labo/n/ned76d2659fb1",
        "x_post_text": (
            "「好きなのに苦しい」はなぜ起きるのか。\n"
            "精神科医・心理学者・脳科学者が、まず話を聞き、それから悩みのしくみを解いてみました。\n\n"
            "#恋愛 #心理学 #脳科学 #お悩み解決"
        ),
        "color_start": (240, 98, 146),
        "color_end": (123, 31, 162),
        "status": "published",  # draft -> published
    },
    "work": {
        "genre_label": "仕事の悩み",
        "thumbnail_title": "頑張るほど苦しい、その理由",
        "article_path": r"C:\Users\admin\Documents\Codex\2026-08-07\note-worry-method\note_work_worry_article_1.md",
        "note_url": "https://note.com/soudan_labo/n/n0d0899ffd973",
        "x_post_text": (
            "「頑張っているのに苦しい」はなぜ起きるのか。\n"
            "精神科医・心理学者・脳科学者が、まず話を聞き、それから仕事の悩みのしくみを解いてみました。\n\n"
            "#仕事の悩み #キャリア相談 #心理学 #脳科学 #お悩み解決"
        ),
        "color_start": (66, 165, 245),
        "color_end": (21, 101, 192),
        "status": "published",
    },
    "relationship": {
        "genre_label": "人間関係の悩み",
        "thumbnail_title": "人間関係の悩み、聞いてから解く",
        "article_path": r"C:\Users\admin\Documents\Codex\2026-08-07\note-worry-method\note_relationship_worry_article_1.md",
        "note_url": "https://note.com/soudan_labo/n/n8c8fcc6b9de5",
        "x_post_text": (
            "職場や友人関係で相手の顔色をうかがってしまう。それはなぜか。\n"
            "精神科医・心理学者・脳科学者が、まず話を聞き、それから悩みのしくみを解いてみました。\n\n"
            "#人間関係 #人間関係の悩み #心理学 #脳科学 #HSP"
        ),
        "color_start": (77, 182, 172),
        "color_end": (0, 105, 92),
        "status": "published",
    },
    "money": {
        "genre_label": "お金の悩み",
        "thumbnail_title": "お金の不安、聞いてから解決",
        "article_path": r"C:\Users\admin\Documents\Codex\2026-08-07\note-worry-method\note_money_worry_article_1.md",
        "note_url": "https://note.com/soudan_labo/n/n787ebd1723a3",
        "x_post_text": (
            "お金の不安が消えないのはなぜか。\n"
            "精神科医・心理学者・脳科学者が、まず話を聞き、それから悩みのしくみを解いてみました。\n\n"
            "#お金の悩み #家計管理 #心理学 #脳科学 #お悩み解決"
        ),
        "color_start": (255, 179, 0),
        "color_end": (230, 81, 0),
        "status": "published",
    },
    "selfesteem": {
        "genre_label": "自己肯定感の悩み",
        "thumbnail_title": "自分を好きになれない理由",
        "article_path": r"C:\Users\admin\Documents\Codex\2026-08-07\note-worry-method\note_selfesteem_worry_article_1.md",
        "note_url": "https://note.com/soudan_labo/n/n51cd8a6629bc",
        "x_post_text": (
            "「自分なんて」が頭から離れない。\n"
            "精神科医・心理学者・脳科学者が、まず話を聞き、それから自己肯定感の悩みのしくみを解いてみました。\n\n"
            "#自己肯定感 #心理学 #脳科学 #お悩み解決 #自己理解"
        ),
        "color_start": (126, 87, 194),
        "color_end": (69, 39, 160),
        "status": "published",
    },
}
