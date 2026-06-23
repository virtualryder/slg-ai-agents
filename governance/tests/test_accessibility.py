from governance.accessibility.wcag import check_html, check_plain_language

def test_img_without_alt_flagged():
    assert not check_html('<img src="x.png">').passes

def test_img_with_alt_passes():
    assert check_html('<img src="x.png" alt="City logo">').passes

def test_heading_skip_flagged():
    assert not check_html("<h1>A</h1><h3>B</h3>").passes

def test_vague_link_flagged():
    assert not check_html('<a href="/x">click here</a>').passes

def test_plain_language_grade():
    assert check_plain_language("Set out your cart by 7 AM on your day.").passes
