import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET
from PIL import Image
from scripts.pinterest import build_rss as m


def item(pid=512, date="Tue, 13 Oct 2026 09:21:16 +0000",
         url="https://www.survival40.com/40s-eye-strain-massage-breaks/?utm_source=rss&utm_medium=rss&utm_campaign=40s-eye-strain-massage-breaks",
         title="眼精疲労に目のマッサージは効く？40代男性の疲れ目対策と休憩のコツ"):
    x = ET.Element("item")
    ET.SubElement(x,"title").text = title
    ET.SubElement(x,"link").text = url
    ET.SubElement(x,"pubDate").text = date
    ET.SubElement(x,"description").text = (
        "<p>日本眼科学会や厚生労働省の資料をもとに、40代男性の疲れ目対策や休憩の目安を解説。</p>"
        "<p>The post a test appeared on Survival40.</p>"
    )
    ET.SubElement(x,"guid", {"isPermaLink":"false"}).text = "https://www.survival40.com/?p=" + str(pid)
    ET.SubElement(x,"{com-wordpress:feed-additions:1}post-id").text = str(pid)
    return x


def make_feed(items):
    root = ET.Element("rss",{"version":"2.0"})
    ch = ET.SubElement(root,"channel")
    for i in items: ch.append(i)
    return ET.tostring(root,encoding="utf-8")


class PinterestRssTests(unittest.TestCase):
    def test_parse_public_wordpress_rss_and_remove_tracking(self):
        p = m.verify_rss_item(item())
        self.assertEqual(p["id"],512)
        self.assertEqual(p["link"],"https://www.survival40.com/40s-eye-strain-massage-breaks/")
        self.assertIn("厚生労働省",p["excerpt"])
        self.assertNotIn("The post",p["excerpt"])
        self.assertTrue(p["has_ads"])

    def test_reject_untrusted_links_and_invalid_items(self):
        link = "https://www.survival40.com/valid/"
        for bad in (
            "http://www.survival40.com/valid/",
            "https://survival40.com/valid/",
            "https://www.survival40.com.evil.test/valid/",
            "https://www.survival40.com/valid/?utm_source=evil",
            "https://www.survival40.com/valid/?foo=bar",
            "https://www.survival40.com/valid/evil/",
        ):
            self.assertIsNone(m.verify_rss_item(item(url=bad)), bad)
        badid = item()
        badid.find("{com-wordpress:feed-additions:1}post-id").text="513"
        self.assertIsNone(m.verify_rss_item(badid))
        self.assertIsNone(m.verify_rss_item(item(date="Fri, 17 Oct 2099 09:21:16 +0000")))
        self.assertIsNone(m.verify_rss_item(item(title="Title")))

    def test_rest_published_canonical_guid_and_fail_closed(self):
        new = item(pid=606,
                   date="Sun, 18 Oct 2026 09:36:53 +0000",
                   url="https://www.survival40.com/40s-spu-style-up-subscription/")
        new.find("guid").text = "https://www.survival40.com/40s-spu-style-up-subscription/"
        parsed = m.verify_rss_item(new)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["id"], 606)
        self.assertEqual(parsed["link"], new.findtext("guid"))
        # A different claimed-domain URL cannot impersonate this item.
        new.find("guid").text = "https://www.survival40.com/other-post/"
        self.assertIsNone(m.verify_rss_item(new))
        # A legacy ?p=ID must still agree with the WordPress namespace ID.
        new.find("guid").text = "https://www.survival40.com/?p=607"
        self.assertIsNone(m.verify_rss_item(new))
        # Other query, external domain, or a non-positive post-id is invalid.
        new.find("guid").text = "https://www.survival40.com/?p=606&x=1"
        self.assertIsNone(m.verify_rss_item(new))
        new.find("guid").text = "https://evil.example/40s-spu-style-up-subscription/"
        self.assertIsNone(m.verify_rss_item(new))
        new.find("guid").text = parsed["link"]
        new.find("{com-wordpress:feed-additions:1}post-id").text = "0"
        self.assertIsNone(m.verify_rss_item(new))

    def test_feed_selection_one_seed_then_new_articles_no_backfill(self):
        base = item()
        old = item(pid=450, date="Tue, 06 Oct 2026 15:42:05 +0000",
                   url="https://www.survival40.com/protein/")
        newer = item(pid=701,date="Thu, 15 Oct 2026 15:01:00 +0000",
                     url="https://www.survival40.com/new-article/")
        first_pin = item(pid=393, date="Thu, 15 Oct 2026 15:01:00 +0000",
                         url="https://www.survival40.com/first-article/")
        with patch.object(m,"request_bytes",return_value=make_feed([base,old,newer,first_pin])):
            selected = m.collect()
            self.assertEqual({p["id"] for p in selected},{512,701})

    def test_xml_has_canonical_article_link_and_real_image_enclosure(self):
        p = m.verify_rss_item(item())
        with tempfile.TemporaryDirectory() as tmp:
            images=Path(tmp)
            (images/"512.png").write_bytes(b"sample-image-bytes")
            with patch.object(m,"ASSET_DIR",images):
                raw=m.rss([p])
        parsed=ET.fromstring(raw)
        entry=parsed.find("./channel/item")
        self.assertEqual(entry.findtext("link"),"https://www.survival40.com/40s-eye-strain-massage-breaks/")
        enc=entry.find("enclosure")
        self.assertEqual(enc.get("type"),"image/png")
        self.assertEqual(enc.get("length"),"18")
        self.assertTrue(enc.get("url").endswith("/512.png"))
        self.assertEqual(entry.findtext("guid"),entry.findtext("link"))

    def test_cards_use_existing_shiori_and_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            portrait=Image.new("RGBA",(300,400),(160,0,200,255))
            p=m.verify_rss_item(item())
            with patch.object(m,"ASSET_DIR",Path(tmp)):
                generated=m.render(p,portrait)
                with Image.open(generated) as im:
                    self.assertEqual(im.size,(1000,1500))
                before=generated.read_bytes()
                self.assertEqual(m.render(p,portrait).read_bytes(),before)


if __name__=="__main__":
    unittest.main()
