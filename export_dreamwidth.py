"""
Экспортер постов и комментариев из Dreamwidth в Markdown файлы.
Создан для alezhu (https://alezhu.dreamwidth.org).
"""

import os
import sys
import time
import hashlib
import re
import html
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import xmlrpc.client
from datetime import datetime, timedelta
import warnings
try:
    from bs4 import MarkupResemblesLocatorWarning
    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
except ImportError:
    pass

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

try:
    from markdownify import markdownify as md
except ImportError:
    def md(html_text):
        text = re.sub(r'<br\s*/?>', '\n', html_text)
        text = re.sub(r'</p>', '\n\n', text)
        text = re.sub(r'<p[^>]*>', '', text)
        text = re.sub(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', text)
        text = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', text)
        text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text)
        text = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', text)
        text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text)
        text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text)
        text = re.sub(r'<pre[^>]*>(.*?)</pre>', r'```\n\1\n```', text, flags=re.DOTALL)
        return html.unescape(text)

USERNAME = "alezhu"
SERVER = "www.dreamwidth.org"
BASE_DIR = r"d:\Sync\OneDrive\Private\Blogs\alezhu\Блог alezhu"
KEY_FILE = os.path.join(BASE_DIR, "dreamwidth.key")
OUTPUT_DIR = BASE_DIR

def to_str(val):
    if isinstance(val, xmlrpc.client.Binary):
        return val.data.decode('utf-8', errors='replace')
    elif isinstance(val, bytes):
        return val.decode('utf-8', errors='replace')
    elif val is None:
        return ""
    return str(val)

def get_api_key():
    if not os.path.exists(KEY_FILE):
        raise FileNotFoundError(f"Файл ключа не найден: {KEY_FILE}")
    with open(KEY_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def sanitize_filename(name):
    # Удаляем запрещенные в Windows символы: \ / : * ? " < > |
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = clean.replace("\n", " ").replace("\r", " ").strip()
    return clean[:120] if clean else "post"

def call_xmlrpc(method_name, params, api_key, max_retries=5):
    url = f"https://{SERVER}/interface/xmlrpc"
    backoff = 3
    for attempt in range(1, max_retries + 1):
        try:
            # 1. Получаем challenge
            chal_body = xmlrpc.client.dumps((), 'LJ.XMLRPC.getchallenge').encode('utf-8')
            req = urllib.request.Request(
                url,
                data=chal_body,
                headers={
                    'User-Agent': 'JBackup/1.0',
                    'Content-Type': 'text/xml'
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                chal_tuple, _ = xmlrpc.client.loads(resp.read())
                chal_res = chal_tuple[0]
            
            challenge = chal_res['challenge']
            auth_response = hashlib.md5(
                (challenge + hashlib.md5(api_key.encode('utf-8')).hexdigest()).encode('utf-8')
            ).hexdigest()

            full_params = {
                'username': USERNAME,
                'auth_method': 'challenge',
                'auth_challenge': challenge,
                'auth_response': auth_response,
                'ver': 1
            }
            full_params.update(params)

            # 2. Вызываем метод
            method_body = xmlrpc.client.dumps((full_params,), f'LJ.XMLRPC.{method_name}').encode('utf-8')
            req2 = urllib.request.Request(
                url,
                data=method_body,
                headers={
                    'User-Agent': 'JBackup/1.0',
                    'Content-Type': 'text/xml'
                }
            )
            with urllib.request.urlopen(req2, timeout=45) as resp2:
                res_tuple, _ = xmlrpc.client.loads(resp2.read())
                return res_tuple[0]

        except Exception as e:
            err_str = str(e)
            # Если 406 - повторный запрос без изменений, возвращаем пустой результат
            if "Client is making repeated requests" in err_str:
                print(f"[{method_name}] Нет новых данных (сервер вернул 406 repeated requests).")
                return {}
            print(f"Ошибка вызова {method_name}: {e}. Ожидание {backoff}с...")
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)

    raise RuntimeError(f"Не удалось выполнить {method_name} после {max_retries} попыток.")

def get_session(api_key):
    try:
        res = call_xmlrpc('sessiongenerate', {'expiration': 'short'}, api_key)
        return res.get('ljsession')
    except Exception as e:
        print(f"Предупреждение: sessiongenerate вернул ошибку: {e}")
        return None

def fetch_comments_xml(session, mode, start_id, num_items=1000):
    url = f"https://{SERVER}/export_comments?get={mode}&startid={start_id}&numitems={num_items}&authas={USERNAME}"
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'JBackup/1.0',
            'Cookie': f'ljsession={session}'
        }
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            print(f"Ошибка загрузки комментариев ({mode}, start={start_id}): {e}. Повтор...")
            time.sleep(3)
    return ""

def load_all_comments(api_key):
    session = get_session(api_key)
    if not session:
        return {}

    comments_by_post = {}
    usermap = {}
    meta_comments = {}

    # 1. Скачиваем мета-информацию комментариев
    next_id = 1
    while next_id:
        xml_data = fetch_comments_xml(session, 'comment_meta', next_id, 1000)
        if not xml_data:
            break
        try:
            root = ET.fromstring(xml_data)
        except Exception as e:
            break

        for u in root.findall('.//usermap'):
            uid = u.attrib.get('id')
            user = u.attrib.get('user')
            if uid and user:
                usermap[uid] = user

        for c in root.findall('.//comment'):
            cid = c.attrib.get('id')
            posterid = c.attrib.get('posterid')
            state = c.attrib.get('state', 'A')
            meta_comments[cid] = {
                'id': cid,
                'poster': usermap.get(posterid, 'Anonymous'),
                'state': state
            }

        next_elem = root.find('.//nextid')
        if next_elem is not None and next_elem.text:
            next_id = int(next_elem.text)
        else:
            break

    if not meta_comments:
        return {}

    # 2. Скачиваем тела комментариев
    next_id = 1
    while next_id:
        xml_data = fetch_comments_xml(session, 'comment_body', next_id, 1000)
        if not xml_data:
            break
        try:
            root = ET.fromstring(xml_data)
        except Exception as e:
            break

        for c in root.findall('.//comment'):
            cid = c.attrib.get('id')
            jitemid = c.attrib.get('jitemid')
            parentid = c.attrib.get('parentid', '0')
            body_text = c.findtext('body') or ''
            subject_text = c.findtext('subject') or ''
            date_text = c.findtext('date') or ''

            meta = meta_comments.get(cid, {})
            poster = meta.get('poster', 'Anonymous')

            comment_obj = {
                'id': cid,
                'parentid': parentid,
                'poster': poster,
                'date': date_text,
                'subject': subject_text,
                'body': body_text
            }

            if jitemid:
                comments_by_post.setdefault(jitemid, []).append(comment_obj)

        next_elem = root.find('.//nextid')
        if next_elem is not None and next_elem.text:
            next_id = int(next_elem.text)
        else:
            break

    return comments_by_post

def clean_dreamwidth_markup(text):
    # Обработка тегов cut: <cut text="..."> или <cut>
    text = re.sub(r'<cut(?:\s+text="([^"]*)")?\s*>', r'\n\n<!--more \1-->\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</cut>', '\n\n', text, flags=re.IGNORECASE)

    # Обработка юзертегов <user name="username"> или <user user="username">
    def replace_user(m):
        u = m.group(1) or m.group(2)
        site = m.group(3) or 'dreamwidth.org'
        return f"[@{u}](https://{u}.{site})"

    text = re.sub(r'<user\s+(?:name|user)="([^"]+)"(?:\s+site="([^"]+)")?\s*/?>', replace_user, text, flags=re.IGNORECASE)

    # Обработка raw-code
    text = re.sub(r'<raw-code>(.*?)</raw-code>', r'```\n\1\n```', text, flags=re.DOTALL | re.IGNORECASE)

    return text

def format_comment_tree(comments, parent_id="0", level=0):
    res = []
    children = [c for c in comments if c.get('parentid', '0') == parent_id]
    prefix = "> " * (level + 1)

    for c in children:
        poster = c.get('poster', 'Anonymous')
        dt = c.get('date', '')
        subj = c.get('subject', '').strip()
        body = c.get('body', '').strip()
        body_md = md(clean_dreamwidth_markup(body)).strip()

        res.append(f"{prefix}**{poster}** ({dt})" + (f" — *{subj}*" if subj else ""))
        res.append(f"{prefix}")
        for line in body_md.splitlines():
            res.append(f"{prefix}{line}")
        res.append(f"{prefix}")

        sub_tree = format_comment_tree(comments, parent_id=c['id'], level=level+1)
        if sub_tree:
            res.extend(sub_tree)

    return res

def export_all():
    api_key = get_api_key()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Экспорт блога {USERNAME} в: {OUTPUT_DIR}\n")

    # 1. Загрузка списка всех элементов блога через syncitems
    print("Получение карты записей (syncitems)...")
    sync_res = call_xmlrpc('syncitems', {'lastsync': ''}, api_key)
    sync_items = sync_res.get('syncitems', [])
    total_sync = len(sync_items)
    print(f"Всего записей на сервере: {total_sync}")

    if total_sync == 0:
        print("Записей не обнаружено.")
        return

    # Карта: itemid -> sync_time
    sync_time_map = {}
    for s in sync_items:
        if s.get('item', '').startswith('L-'):
            try:
                iid = int(s['item'][2:])
                sync_time_map[iid] = s['time']
            except ValueError:
                pass

    max_sync_time = sync_items[-1]['time']

    # 2. Скачивание комментариев
    print("Проверка комментариев...")
    comments_by_post = load_all_comments(api_key)
    if comments_by_post:
        print(f"Найдено комментариев к {len(comments_by_post)} постам.")
    else:
        print("Комментариев не обнаружено или комментарии пустые.")

    # 3. Скачивание самих постов
    last_sync = ""
    total_downloaded = 0
    saved_filenames = set()

    while True:
        events_res = call_xmlrpc('getevents', {
            'selecttype': 'syncitems',
            'lastsync': last_sync,
            'ver': 1,
            'lineendings': 'unix',
            'noprops': 0
        }, api_key)

        events = events_res.get('events', [])
        if not events:
            break

        for evt in events:
            item_id = str(evt.get('itemid', ''))
            subject = to_str(evt.get('subject')).strip()
            if not subject:
                subject = f"Запись {item_id}"
            
            raw_event = to_str(evt.get('event'))
            event_time = to_str(evt.get('eventtime'))
            security = to_str(evt.get('security')) or 'public'
            props = evt.get('props', {})

            # Метаданные
            taglist = to_str(props.get('taglist', ''))
            tags = [t.strip() for t in taglist.split(',')] if taglist else []
            music = to_str(props.get('current_music', ''))
            mood = to_str(props.get('current_mood', ''))

            # Преобразование текста в Markdown
            cleaned_html = clean_dreamwidth_markup(raw_event)
            body_md = md(cleaned_html).strip()

            # Имя файла: YYYY-MM-DD - Название.md
            date_prefix = event_time[:10] if len(event_time) >= 10 else "post"
            safe_title = sanitize_filename(subject)
            base_filename = f"{date_prefix} - {safe_title}"
            filename = f"{base_filename}.md"
            if filename in saved_filenames:
                filename = f"{base_filename} ({item_id}).md"
            saved_filenames.add(filename)

            filepath = os.path.join(OUTPUT_DIR, filename)

            # Формирование содержимого Markdown
            content = []
            content.append("---")
            content.append(f'title: "{subject.replace(chr(34), chr(39))}"')
            content.append(f"date: {event_time}")
            content.append(f"id: {item_id}")
            content.append(f"url: https://{USERNAME}.dreamwidth.org/{item_id}.html")
            content.append(f"security: {security}")
            if tags:
                content.append("tags:")
                for t in tags:
                    content.append(f"  - {t}")
            if music:
                content.append(f'music: "{music.replace(chr(34), chr(39))}"')
            if mood:
                content.append(f'mood: "{mood.replace(chr(34), chr(39))}"')
            content.append("---\n")

            content.append(f"# {subject}\n")
            content.append(body_md)

            # Музыка / Настроение
            extras = []
            if music:
                extras.append(f"*Музыка:* {music}")
            if mood:
                extras.append(f"*Настроение:* {mood}")
            if extras:
                content.append("\n\n" + " | ".join(extras))

            # Комментарии
            post_comments = comments_by_post.get(item_id, [])
            if post_comments:
                content.append("\n\n---\n### Комментарии:\n")
                comment_lines = format_comment_tree(post_comments)
                content.extend(comment_lines)

            # Сохранение файла
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(content) + "\n")

            total_downloaded += 1
            print(f"[{total_downloaded}/{total_sync}] {filename}")

        # Условие завершения или переход к следующей пачке
        if len(events) < 100 or total_downloaded >= total_sync:
            break

        max_logtime = max(to_str(e.get('logtime', '')) for e in events)
        try:
            dt = datetime.strptime(max_logtime, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)
            last_sync = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            last_sync = max_logtime

    print(f"\n==========================================")
    print(f"Успешно завершено!")
    print(f"Экспортировано {total_downloaded} постов в: {OUTPUT_DIR}")
    print(f"==========================================")

if __name__ == "__main__":
    export_all()
