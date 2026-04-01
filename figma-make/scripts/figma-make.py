# -*- coding: utf-8 -*-
"""
Figma Make 自动化脚本
功能：自动打开 Figma Web，在草稿箱创建 FigmaMake，输入设计需求并生成设计稿
"""

import os
import sys
import time
import json
from pathlib import Path

# 修复 Windows 控制台编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ============================================================
# 设计需求 Prompt（可修改此处来改变生成的设计稿内容）
# ============================================================
DESIGN_PROMPT = """Design a game official website homepage inspired by World of Warcraft China official site style.

Theme: Dark fantasy, epic and cinematic atmosphere
Colors: Deep navy/black background (#060E1E), gold accents (#C8A84B, #F0C040), blue highlights
Typography: Display/serif fonts for headings, clean sans-serif for body text

Layout sections (1920px wide):
1. Top navigation bar - game logo left, menu links center, login button and language switcher right
2. Full-width hero banner (1920x900px) - epic dark fantasy game artwork background, large dramatic headline text, subtitle, primary CTA button with glow effect, particle/light beam decorative effects
3. Latest news & updates section - 3 cards in a row, each with image thumbnail, category tag, title, date
4. Game features section - 3 feature blocks with icons, bold titles, short descriptions
5. Footer - logo, navigation links, social media icons, copyright text

Visual details:
- Gold gradient borders and dividers between sections
- Hover states: golden glow on buttons, underline on nav links
- Corner ornament decorations (fantasy style)
- Subtle grid/texture overlay on dark backgrounds
- Drop shadow and inner glow effects on key elements"""

# ============================================================
# 配置
# ============================================================
SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"
SESSION_FILE = Path(__file__).parent.parent / "figma-session.json"
FIGMA_DRAFTS_URL = "https://www.figma.com/files/recents-and-sharing/drafts"

# ============================================================
# 工具函数
# ============================================================
def save_screenshot(page, name: str):
    """保存截图用于调试"""
    path = SCREENSHOTS_DIR / f"{name}.png"
    page.screenshot(path=str(path))
    print(f"  [截图] {path.name}")


def find_and_click_make_button(page) -> bool:
    """多策略查找 FigmaMake 入口"""
    print("\n  查找 FigmaMake 入口...")

    selectors = [
        "button:has-text('Make')",
        "[data-testid*='make']",
        "a:has-text('Make')",
        "[aria-label*='Make']",
        "button:has-text('AI')",
        "button:has-text('Figma AI')",
    ]

    for selector in selectors:
        try:
            el = page.query_selector(selector)
            if el and el.is_visible():
                print(f"  [OK] 找到入口: {selector}")
                el.click()
                return True
        except Exception:
            continue

    return False


def find_make_in_new_menu(page) -> bool:
    """通过新建菜单查找 FigmaMake"""
    print("  尝试通过新建菜单查找...")

    new_selectors = [
        "button:has-text('New design file')",
        "button:has-text('New')",
        "[data-testid='new-file-button']",
        "[aria-label='New file']",
    ]

    clicked = False
    for selector in new_selectors:
        try:
            el = page.query_selector(selector)
            if el and el.is_visible():
                el.click()
                clicked = True
                print(f"  [OK] 点击新建: {selector}")
                time.sleep(1)
                break
        except Exception:
            continue

    if not clicked:
        print("  [ERR] 未找到新建按钮")
        return False

    save_screenshot(page, "02_new_menu")
    time.sleep(0.5)

    make_selectors = [
        "[role='menuitem']:has-text('Make')",
        "li:has-text('Make')",
        "button:has-text('Make')",
        "[role='option']:has-text('Make')",
        ":has-text('Make')",
    ]

    for selector in make_selectors:
        try:
            el = page.query_selector(selector)
            if el and el.is_visible():
                el.click()
                print(f"  [OK] 在菜单中找到 Make: {selector}")
                return True
        except Exception:
            continue

    return False


def input_prompt_and_generate(page) -> bool:
    """输入设计 Prompt 并提交"""
    print("\n  输入设计需求...")

    input_selectors = [
        "textarea[placeholder*='Describe']",
        "textarea[placeholder*='describe']",
        "textarea[placeholder*='design']",
        "[contenteditable='true']",
        "textarea",
        "[role='textbox']",
    ]

    input_el = None
    for selector in input_selectors:
        try:
            page.wait_for_selector(selector, timeout=15000)
            el = page.query_selector(selector)
            if el and el.is_visible():
                input_el = el
                print(f"  [OK] 找到输入框: {selector}")
                break
        except PlaywrightTimeoutError:
            continue

    if not input_el:
        print("  [ERR] 未找到 FigmaMake 输入框")
        save_screenshot(page, "03_input_failed")
        return False

    save_screenshot(page, "03_make_input")
    input_el.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    time.sleep(0.3)
    page.keyboard.type(DESIGN_PROMPT, delay=10)
    print(f"  [OK] Prompt 输入完成 ({len(DESIGN_PROMPT)} 字符)")

    time.sleep(1)
    save_screenshot(page, "03_make_input_filled")

    submit_selectors = [
        "button:has-text('Generate')",
        "button:has-text('Create')",
        "button:has-text('Make')",
        "button[type='submit']",
        "[data-testid*='submit']",
        "[data-testid*='generate']",
        "button[aria-label*='submit']",
        "button[aria-label*='generate']",
        "button svg + *",
        "form button:last-child",
    ]

    for selector in submit_selectors:
        try:
            el = page.query_selector(selector)
            if el and el.is_visible() and el.is_enabled():
                el.click()
                print(f"  [OK] 点击生成按钮: {selector}")
                return True
        except Exception:
            continue

    print("  [INFO] 未找到提交按钮，尝试 Enter 键...")
    try:
        for selector in ["textarea:visible", "[contenteditable='true']:visible", "[role='textbox']:visible"]:
            fresh_el = page.query_selector(selector)
            if fresh_el:
                fresh_el.focus()
                time.sleep(0.2)
                page.keyboard.press("Control+Enter")
                print(f"  [INFO] 按下 Ctrl+Enter 提交")
                time.sleep(1)
                page.keyboard.press("Enter")
                return True
    except Exception as e:
        print(f"  [WARN] Enter 提交失败: {e}")

    save_screenshot(page, "03_need_manual_submit")
    print("\n  [!] 请在浏览器中手动点击生成按钮，然后按 Enter 继续脚本")
    try:
        input("  按 Enter 继续...")
    except EOFError:
        pass
    return True


def wait_for_generation(page) -> str:
    """等待 AI 生成完成"""
    print("\n  等待 AI 生成（最长 5 分钟）...")
    save_screenshot(page, "04_generating")

    start = time.time()
    last_url = page.url

    while time.time() - start < 300:
        time.sleep(5)
        cur_url = page.url

        if cur_url != last_url and "figma.com" in cur_url:
            print(f"  [OK] 页面跳转到: {cur_url}")
            save_screenshot(page, "05_done")
            return cur_url

        elapsed = int(time.time() - start)
        if elapsed % 30 == 0:
            print(f"  [等待] {elapsed}s...")
            save_screenshot(page, f"04_generating_{elapsed}s")

    save_screenshot(page, "05_timeout")
    return page.url


def save_session(context):
    """保存登录态供下次使用"""
    storage = context.storage_state()
    with open(SESSION_FILE, "w") as f:
        json.dump(storage, f)
    print(f"  [OK] 登录态已保存: {SESSION_FILE}")


def main():
    print("=" * 50)
    print("  Figma Make 自动化脚本")
    print("=" * 50)

    SCREENSHOTS_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:

        print("\n[1/5] 启动浏览器...")
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )

        if SESSION_FILE.exists():
            print(f"  [INFO] 找到已保存的登录态，自动加载")
            with open(SESSION_FILE) as f:
                storage_state = json.load(f)
            context = browser.new_context(
                storage_state=storage_state,
                viewport={"width": 1440, "height": 900},
            )
        else:
            context = browser.new_context(viewport={"width": 1440, "height": 900})

        page = context.new_page()

        print("\n[2/5] 打开 Figma 草稿箱...")
        page.goto(FIGMA_DRAFTS_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        save_screenshot(page, "01_figma_home")

        if "login" in page.url or "signup" in page.url or "auth" in page.url:
            print("\n  [!] 需要登录 Figma")
            print("  请在弹出的浏览器窗口中手动登录 Figma 账号")
            print("  登录完成后，脚本会自动继续...")
            print("  等待最长 3 分钟...")
            try:
                page.wait_for_url("**/files/**", timeout=180000)
            except PlaywrightTimeoutError:
                page.goto(FIGMA_DRAFTS_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            save_session(context)

        print(f"  [OK] 当前页面: {page.url[:60]}")

        print("\n[3/5] 查找 FigmaMake 入口...")
        found = find_and_click_make_button(page)
        if not found:
            found = find_make_in_new_menu(page)

        if not found:
            print("\n  [ERR] 无法找到 FigmaMake 入口")
            print(f"  请查看截图: {SCREENSHOTS_DIR}")
            print("  可能原因：账号无 FigmaMake 权限，或 Figma UI 已更新")
            try:
                input("\n  按 Enter 退出...")
            except EOFError:
                pass
            save_session(context)
            browser.close()
            return

        time.sleep(2)

        print("\n[4/5] 输入设计需求...")
        success = input_prompt_and_generate(page)

        if not success:
            print("\n  [ERR] Prompt 输入失败，请检查截图")
            try:
                input("\n  按 Enter 退出...")
            except EOFError:
                pass
            save_session(context)
            browser.close()
            return

        print("\n[5/5] 等待 AI 生成设计稿...")
        final_url = wait_for_generation(page)

        save_session(context)

        print("\n" + "=" * 50)
        print("  完成！")
        print(f"  文件 URL: {final_url}")
        print(f"  截图目录: {SCREENSHOTS_DIR}")
        print("=" * 50)

        try:
            input("\n  按 Enter 关闭浏览器...")
        except EOFError:
            pass
        browser.close()


if __name__ == "__main__":
    main()
