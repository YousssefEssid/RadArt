from app.utils.text_clean import (
    attractive_cluster_label,
    clean_display_title,
    clean_plain_text,
    is_junk_keyword,
)


def test_strips_img_and_urls_from_body():
    raw = (
        '«#8217, #8220, #8221» monte '
        '<p><img alt="" class="attachment-full size-full wp-post-image" '
        'src="https://www.nme.com/wp-content/uploads/2026/08/x.jpg" /></p> '
        "En Tunisie la fenêtre est courte."
    )
    out = clean_plain_text(raw)
    assert "<img" not in out.lower()
    assert "nme.com" not in out
    assert "wp-post-image" not in out
    assert "Tunisie" in out
    assert "’" in out or "'" in out or "“" in out or '"' in out


def test_title_no_entity_codes_or_urls():
    dirty = "“#8230, https://realites.com.tn/fr, Faouzi Ben Sadok Benzarti”"
    title = clean_display_title(dirty)
    assert "http" not in title.lower()
    assert "8230" not in title
    assert "realites.com" not in title.lower()
    assert "Faouzi" in title or "Benzarti" in title


def test_css_hex_and_target_junk():
    dirty = "“#6f6f6f, target=, afrobasket”"
    title = clean_display_title(dirty)
    assert "6f6f6f" not in title.lower()
    assert "target" not in title.lower()
    assert "afrobasket" in title.lower()


def test_junk_keywords_filtered():
    assert is_junk_keyword("#8217")
    assert is_junk_keyword("8220")
    assert is_junk_keyword("#6f6f6f")
    assert is_junk_keyword("target")
    assert not is_junk_keyword("afrobasket")
    assert not is_junk_keyword("tunisia")


def test_attractive_label_prefers_headline():
    label = attractive_cluster_label(
        ["Faouzi Ben Sadok Benzarti sur le banc"],
        ["#8217", "#8220", "afrobasket"],
    )
    assert "8217" not in label
    assert "Faouzi" in label or "afrobasket" in label.lower()
