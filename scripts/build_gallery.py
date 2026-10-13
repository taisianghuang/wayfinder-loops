#!/usr/bin/env python3
"""Build the #35 prototype gallery as one self-contained HTML page.

The frontend repo is private, so `gh` cannot serve the PNGs to a browser.
Every frame is embedded as a data URI instead.
"""
import base64
import pathlib

SHOTS = pathlib.Path("/home/tai/wayfinder-lab/wt-35-prototype/docs/prototype/35")
OUT = pathlib.Path("/home/tai/.claude/jobs/4108a78f/tmp/p1-company-picker.html")


def uri(name: str) -> str:
    data = base64.b64encode((SHOTS / f"{name}.png").read_bytes()).decode()
    return f"data:image/png;base64,{data}"


SECTIONS = [
    {
        "count": "n = 1",
        "title": "只有一家公司的人",
        "verdict": "建議：這一屏不出現，頁首也不放切換入口",
        "note": "他沒有第二個選項，選公司這一屏對他來說是一次白按。頁首那一行也一樣——「切換」按下去只會看到自己唯一的那家公司，"
                "所以公司名維持今天的樣子：右上角一行小字，不佔按鈕位置。",
        "frames": [
            ("one-pick", "選公司屏（假設真的出現）",
             "只有一張卡，下面整片空白。這張圖是給你比對用的，不是建議的樣子。"),
            ("one-report-no-bar", "報工頁——建議的樣子",
             "公司名在右上角一行小字，就是今天已經在跑的版面，沒有新東西。"),
            ("one-report-with-bar", "報工頁——放了切換入口",
             "多一條 52px 的頁首列，把整個工作區往下推，換來一顆他永遠不需要按的按鈕。"),
        ],
    },
    {
        "count": "n = 2",
        "title": "兩家公司的人",
        "verdict": "建議：先出選公司屏，選完頁首常駐一行",
        "note": "兩張大卡片，一屏就看完，不用捲。卡片上除了公司名還印他在那家公司的角色——"
                "同一個工人在兩家公司常常是同一個角色，但名字很像的兩家公司（「宏華土木」對「宏華營造」）就靠這一行分辨。",
        "frames": [
            ("two-pick", "選公司屏",
             "整張卡都是按鈕，72px 高，公司名是畫面上最大的字。"),
            ("two-report", "報工頁頁首那一行",
             "「目前 大安營造」加一顆 44px 的〔切換〕。切換是外框中性按鈕，不是藍字連結——這一頁的藍已經花在右下角〔複核明細〕。"),
            ("two-switch-back", "按下〔切換〕之後",
             "回到同一屏，目前那家標上「目前」，最下面多一顆〔不換，回報工頁〕。沒有新畫面要設計。"),
        ],
    },
    {
        "count": "n = 5",
        "title": "五家公司的人",
        "verdict": "放得下：五張卡在 iPhone 14 上一屏看完，還剩約 270px",
        "note": "這裡是 LIFF 網頁不是 LINE 泡泡，捲動本來就免費，所以「放不放得下」不是硬上限、只是要不要捲一下的問題。"
                "實測到八家才開始被切到（見下面那一組），所以五家完全不用另外設計形狀。",
        "frames": [
            ("five-pick", "選公司屏",
             "第三張卡是刻意放的長公司名，會折成兩行、把卡撐高，不會被切掉。"),
            ("five-report", "報工頁頁首那一行",
             "跟兩家的人完全一樣——公司數量不影響選完之後的版面。"),
        ],
    },
    {
        "count": "n = 8",
        "title": "壓力測試：八家公司",
        "verdict": "八家才開始要捲，而且只捲一點",
        "note": "不是這張票問的四種人，放在這裡是為了給「五家放得下嗎」一個邊界。八家的時候最後一張卡剛好被螢幕底切到，"
                "捲一下就到底，不需要搜尋框、不需要分頁。",
        "frames": [
            ("eight-pick", "選公司屏——最上面",
             "第八張卡（順泰起重）在畫面底部被切掉一角，這是唯一提示還有東西的地方。"),
            ("eight-pick-bottom", "捲到底",
             "只捲了十幾個 pixel 就到底。真的要處理的話，缺的是「還有更多」這件事看不出來，不是塞不下。"),
        ],
    },
    {
        "count": "n = 2，其中 1 家停權",
        "title": "兩家公司但一家已停權的人",
        "verdict": "建議：列出來、灰掉、可以按，按了說原因",
        "note": "不列是最糟的：他會以為公司從系統裡消失了，然後打電話問人。灰掉又按不動也差不多——"
                "會去按灰卡片的人，正好就是需要知道為什麼灰的那個人。所以這張卡不是 disabled，按下去在卡片下面直接長出一行說明。",
        "frames": [
            ("suspended-pick", "選公司屏",
             "停權那張卡退到底色、公司名轉灰、右邊的箭頭收掉，狀態由「已停權」這三個字講，不是只靠顏色。"),
            ("suspended-pick-tapped", "按了停權那張卡",
             "原地長出一行：說清楚不能報工，也說清楚要找誰恢復——找那家公司的管理員，不是找平台。"),
            ("suspended-report", "選了還能用的那家之後",
             "頁首照樣一行。停權的那家仍然留在〔切換〕裡，因為權限恢復之後他還要回去。"),
        ],
    },
]

FINDINGS = [
    ("aria-disabled 會把停權那張卡變成按不動的",
     "第一版把停權卡片寫成 <code>aria-disabled</code>，截圖腳本點不動它——Playwright 認為它 not enabled。"
     "手指在真手機上還是按得到，但輔助工具會照 aria 走。要「按了給說明」就兩個都不能用，狀態改由「已停權」那三個字承擔。"),
    ("CONTEXT.md 早就寫了停權的公司要列出來",
     "<code>Membership</code> 那一條寫「includes suspended ones — render them disabled in the tenant picker」。"
     "所以「列不列」其實已經答過了，這張票真正沒答的是「灰掉之後按下去說什麼」。"),
    ("LIFF 已經有一個選公司的畫面在跑了",
     "綁定頁的 <code>PickCompanyScreen</code>（apps/liff/.../line-binding/screens.tsx）就是同一個形狀，"
     "只是它只列 ACTIVE 的公司、也沒有頁首那一行。定案之後這兩個畫面應該合成一個。"),
    ("頁首那一行會和今天的公司名撞在一起",
     "報工頁的 <code>ReportHeader</code> 今天就在右上角印公司名。頁首列開著的時候公司名會出現兩次，"
     "所以原型裡是「有頁首列就收掉角落那行」——這是一個要你確認的取捨，不是實作細節。"),
    ("這一屏不需要新的後端",
     "<code>switch-tenant</code> 已經在了，<code>me.memberships[]</code> 也已經連停權的一起回。"
     "原型沒打後端，但四種人都是照 <code>MembershipResponse</code> 的真實欄位餵的。"),
]

CARDS = "".join(
    f"""
      <section class="worker">
        <header class="worker-head">
          <p class="eyebrow">{s['count']}</p>
          <h2>{s['title']}</h2>
          <p class="verdict">{s['verdict']}</p>
          <p class="note">{s['note']}</p>
        </header>
        <div class="strip">
          {"".join(f'''
          <figure class="shot">
            <button type="button" class="phone" aria-label="放大：{label}">
              <img src="{uri(name)}" alt="{label}" width="390" height="844" loading="lazy">
            </button>
            <figcaption>
              <span class="shot-label">{label}</span>
              <span class="shot-note">{desc}</span>
            </figcaption>
          </figure>''' for name, label, desc in s['frames'])}
        </div>
      </section>"""
    for s in SECTIONS
)

FINDING_ROWS = "".join(
    f"""
        <div class="finding">
          <h3>{title}</h3>
          <p>{body}</p>
        </div>"""
    for title, body in FINDINGS
)

HTML = f"""<title>P1 選公司原型</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
  :root {{
    --ground: #e8edf1;
    --panel: #ffffff;
    --panel-sunk: #dde5eb;
    --ink: #14202b;
    --ink-soft: #56687a;
    --ink-faint: #8395a4;
    --rule: #c6d3dd;
    --accent: #0f5c7a;
    --accent-soft: #d6e6ee;
    --flag: #8a4a12;
    --flag-soft: #f0e2d4;
    --bezel: #2a3540;
    --shadow: 0 1px 2px rgba(20, 32, 43, .08), 0 8px 24px rgba(20, 32, 43, .07);
    --sans: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif;
    --serif: "Noto Serif TC", "Songti TC", serif;
    --mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", monospace;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --ground: #101820;
      --panel: #1a242e;
      --panel-sunk: #141d25;
      --ink: #e7eef4;
      --ink-soft: #a3b4c2;
      --ink-faint: #74889a;
      --rule: #2c3a47;
      --accent: #6fb8d8;
      --accent-soft: #1e3947;
      --flag: #dda06a;
      --flag-soft: #3a2c1e;
      --bezel: #05090d;
      --shadow: 0 1px 2px rgba(0, 0, 0, .5), 0 10px 30px rgba(0, 0, 0, .4);
    }}
  }}
  :root[data-theme="dark"] {{
    --ground: #101820;
    --panel: #1a242e;
    --panel-sunk: #141d25;
    --ink: #e7eef4;
    --ink-soft: #a3b4c2;
    --ink-faint: #74889a;
    --rule: #2c3a47;
    --accent: #6fb8d8;
    --accent-soft: #1e3947;
    --flag: #dda06a;
    --flag-soft: #3a2c1e;
    --bezel: #05090d;
    --shadow: 0 1px 2px rgba(0, 0, 0, .5), 0 10px 30px rgba(0, 0, 0, .4);
  }}

  body {{
    background: var(--ground);
    color: var(--ink);
    font-family: var(--sans);
    font-size: 15px;
    line-height: 1.75;
    -webkit-font-smoothing: antialiased;
  }}
  .wrap {{
    max-width: 1080px;
    margin: 0 auto;
    padding: 40px 20px 80px;
    display: flex;
    flex-direction: column;
    gap: 40px;
  }}

  .masthead {{
    display: flex;
    flex-direction: column;
    gap: 14px;
    padding-bottom: 32px;
    border-bottom: 2px solid var(--ink);
  }}
  .masthead .eyebrow {{ color: var(--accent); }}
  .masthead h1 {{
    font-family: var(--serif);
    font-weight: 700;
    font-size: clamp(28px, 5vw, 40px);
    line-height: 1.25;
    letter-spacing: -.01em;
    text-wrap: balance;
    margin: 0;
  }}
  .lede {{
    max-width: 62ch;
    color: var(--ink-soft);
    margin: 0;
  }}
  .meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px 20px;
    font-family: var(--mono);
    font-size: 12px;
    color: var(--ink-faint);
  }}
  .meta code {{ font-family: var(--mono); color: var(--ink-soft); }}

  .eyebrow {{
    font-family: var(--mono);
    font-size: 11.5px;
    font-weight: 500;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: var(--ink-faint);
    margin: 0;
  }}

  .worker {{ display: flex; flex-direction: column; gap: 22px; }}
  .worker-head {{ display: flex; flex-direction: column; gap: 8px; }}
  .worker-head h2 {{
    font-family: var(--serif);
    font-weight: 600;
    font-size: clamp(21px, 3.4vw, 27px);
    line-height: 1.3;
    margin: 0;
  }}
  .verdict {{
    align-self: flex-start;
    margin: 2px 0 0;
    padding: 5px 12px;
    border-radius: 2px;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: 13.5px;
    font-weight: 500;
    line-height: 1.5;
  }}
  .worker:last-of-type .verdict {{ background: var(--flag-soft); color: var(--flag); }}
  .note {{ max-width: 64ch; margin: 4px 0 0; color: var(--ink-soft); }}

  .strip {{
    display: flex;
    flex-wrap: wrap;
    gap: 28px;
    align-items: flex-start;
  }}
  .shot {{
    margin: 0;
    flex: 1 1 236px;
    max-width: 292px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}
  .phone {{
    display: block;
    width: 100%;
    padding: 7px;
    border: 0;
    border-radius: 26px;
    background: var(--bezel);
    box-shadow: var(--shadow);
    cursor: zoom-in;
  }}
  .phone img {{
    display: block;
    width: 100%;
    height: auto;
    border-radius: 19px;
  }}
  .phone:focus-visible {{ outline: 3px solid var(--accent); outline-offset: 3px; }}
  figcaption {{ display: flex; flex-direction: column; gap: 3px; }}
  .shot-label {{ font-size: 14px; font-weight: 500; }}
  .shot-note {{ font-size: 13px; line-height: 1.6; color: var(--ink-soft); }}

  .findings {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding-top: 28px;
    border-top: 1px solid var(--rule);
  }}
  .findings > .eyebrow {{ margin-bottom: 14px; }}
  .finding {{
    padding: 16px 0;
    border-bottom: 1px solid var(--rule);
  }}
  .finding:last-child {{ border-bottom: 0; }}
  .finding h3 {{ font-size: 15.5px; font-weight: 700; margin: 0 0 4px; }}
  .finding p {{ margin: 0; max-width: 74ch; color: var(--ink-soft); }}
  .finding code, .howto code {{
    font-family: var(--mono);
    font-size: .88em;
    padding: 1px 4px;
    border-radius: 2px;
    background: var(--panel-sunk);
    color: var(--ink);
  }}

  .howto {{
    background: var(--panel);
    border: 1px solid var(--rule);
    border-radius: 4px;
    padding: 20px 22px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .howto h2 {{ font-family: var(--serif); font-weight: 600; font-size: 19px; margin: 0; }}
  .howto p {{ margin: 0; max-width: 70ch; color: var(--ink-soft); }}
  .howto pre {{
    margin: 4px 0 0;
    padding: 12px 14px;
    overflow-x: auto;
    background: var(--panel-sunk);
    border-radius: 3px;
    font-family: var(--mono);
    font-size: 12.5px;
    line-height: 1.7;
    color: var(--ink);
  }}
  a {{ color: var(--accent); }}

  /* The UA rule for [hidden] is display:none, which `display:flex` below wins
     against — so the overlay needs its own hidden state. */
  #lightbox[hidden] {{ display: none; }}
  #lightbox {{
    position: fixed;
    inset: 0;
    z-index: 50;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background: rgba(8, 14, 20, .88);
    cursor: zoom-out;
  }}
  #lightbox img {{
    max-width: 100%;
    max-height: 100%;
    border-radius: 10px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, .6);
  }}
  @media (max-width: 640px) {{
    .strip {{ gap: 22px; }}
    .shot {{ flex: 1 1 100%; max-width: 340px; }}
  }}
</style>

<div class="wrap">
  <header class="masthead">
    <p class="eyebrow">planning #35 · V1 原型</p>
    <h1>多公司的工人從 LINE 進來，第一屏長什麼樣</h1>
    <p class="lede">
      V1：聊天面完全不動。工人點〔合約報工〕開 LIFF，如果他屬於兩家以上公司，先出一屏「你要用哪一家公司報工？」，
      選了才進報工頁；報工頁頁首常駐一行「目前：○○公司〔切換〕」。下面是四種人各自看到的畫面。
    </p>
    <p class="meta">
      <span>iPhone 14 · <code>390 × 844</code> · 2x</span>
      <span>淺色主題</span>
      <span>共 13 張，點圖可放大</span>
    </p>
  </header>
{CARDS}
  <section class="findings">
    <p class="eyebrow">做的時候發現的事</p>
{FINDING_ROWS}
  </section>

  <section class="howto">
    <h2>自己在手機上點</h2>
    <p>分支 <code>prototype/35-liff-company-picker</code>（不會進 main）。切換器在畫面下緣，可以直接切四種人和頁首列開關。</p>
    <pre>git fetch origin &amp;&amp; git switch prototype/35-liff-company-picker
pnpm install &amp;&amp; pnpm --filter liff dev
# http://localhost:5175/prototype/company-picker</pre>
  </section>
</div>

<script>
  const box = document.createElement("div");
  box.id = "lightbox";
  box.hidden = true;
  const full = document.createElement("img");
  full.alt = "";
  box.append(full);
  document.body.append(box);

  function close() {{
    box.hidden = true;
    full.removeAttribute("src");
  }}

  for (const button of document.querySelectorAll(".phone")) {{
    button.addEventListener("click", () => {{
      full.src = button.querySelector("img").src;
      box.hidden = false;
    }});
  }}
  box.addEventListener("click", close);
  window.addEventListener("keydown", (event) => {{
    if (event.key === "Escape") close();
  }});
</script>
"""

OUT.write_text(HTML, encoding="utf-8")
print(f"{OUT} — {OUT.stat().st_size / 1_000_000:.2f} MB")
