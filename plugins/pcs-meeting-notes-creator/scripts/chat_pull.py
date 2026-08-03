"""PCS Google Chat reader — read-only puller for the weekly work reports.

Usage:
  python chat_pull.py auth                      # one-time OAuth consent (opens YOUR browser)
  python chat_pull.py pull --after 2026-07-23T18:00:00Z --before 2026-07-30T19:00:00Z
  python chat_pull.py pull --days 7             # convenience: last N days

Output: chat_export_<timestamp>.json (full data) + chat_export_<timestamp>.md (readable digest)
written into the exports/ subfolder next to this script.

Read-only scopes only. Never posts, edits, or deletes anything.
"""
import argparse
import datetime as dt
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET = os.path.join(BASE, "client_secret.json")
TOKEN = os.path.join(BASE, "token.json")
EXPORTS = os.path.join(BASE, "exports")

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/chat.spaces.readonly",
    "https://www.googleapis.com/auth/chat.messages.readonly",
    "https://www.googleapis.com/auth/chat.memberships.readonly",
    "https://www.googleapis.com/auth/directory.readonly",
]
NAMES_CACHE = os.path.join(BASE, "names_cache.json")


def get_creds(interactive=False):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
        have = set(json.load(open(TOKEN)).get("scopes") or [])
        if not set(SCOPES).issubset(have):
            if not interactive:
                sys.exit("token.json is missing newly added scopes. Run:  python chat_pull.py auth")
            creds = None
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN, "w") as f:
            f.write(creds.to_json())
        return creds
    if not interactive:
        sys.exit("No valid token. Run:  python chat_pull.py auth")
    if not os.path.exists(CLIENT_SECRET):
        sys.exit(f"Missing {CLIENT_SECRET} - download the OAuth Desktop client JSON "
                 "from Google Cloud console and save it there first.")
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    with open(TOKEN, "w") as f:
        f.write(creds.to_json())
    print("Token saved to token.json - auth complete.")
    return creds


def my_user_id(creds):
    """Google Chat sender names are users/<google-user-id>; OIDC 'sub' is that id."""
    import google.auth.transport.requests
    import requests as _rq  # google-auth vendored transport is enough, but requests is simpler
    try:
        r = _rq.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {creds.token}"},
            timeout=30,
        )
        if r.ok:
            return "users/" + r.json().get("sub", "")
    except Exception:
        pass
    return None


def resolve_names(creds, user_ids):
    """users/<id> -> display name via People API directory profiles; cached locally."""
    cache = {}
    if os.path.exists(NAMES_CACHE):
        try:
            cache = json.load(open(NAMES_CACHE, encoding="utf-8"))
        except Exception:
            cache = {}
    missing = [u for u in user_ids if u and u not in cache]
    if missing:
        from googleapiclient.discovery import build
        people = build("people", "v1", credentials=creds)

        def person_label(person):
            names = person.get("names") or []
            emails = person.get("emailAddresses") or []
            return (names[0].get("displayName") if names else None) or \
                   (emails[0].get("value") if emails else None)

        # Sweep the whole Workspace directory once: id -> display name.
        try:
            token = None
            while True:
                resp = people.people().listDirectoryPeople(
                    sources=["DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE"],
                    readMask="names,emailAddresses,metadata",
                    pageSize=1000, pageToken=token).execute()
                for person in resp.get("people", []):
                    pid = "users/" + person.get("resourceName", "").split("/")[-1]
                    label = person_label(person)
                    if label:
                        cache[pid] = label
                token = resp.get("nextPageToken")
                if not token:
                    break
        except Exception as e:
            print(f"  (directory sweep unavailable: {str(e)[:120]})")

        # Fallback for ids still unresolved (external users, bots).
        still = [u for u in missing if u not in cache]
        for i in range(0, len(still), 50):
            batch = still[i:i + 50]
            try:
                resp = people.people().getBatchGet(
                    resourceNames=["people/" + u.split("/")[-1] for u in batch],
                    personFields="names,emailAddresses",
                    sources=["READ_SOURCE_TYPE_PROFILE"],
                ).execute()
                for r in resp.get("responses", []):
                    person = r.get("person") or {}
                    pid = "users/" + (r.get("requestedResourceName") or person.get("resourceName", "")).split("/")[-1]
                    label = person_label(person)
                    if label:
                        cache[pid] = label
            except Exception:
                continue
        try:
            with open(NAMES_CACHE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=0)
        except Exception:
            pass
    return cache


def list_spaces(svc):
    spaces, token = [], None
    while True:
        resp = svc.spaces().list(pageSize=1000, pageToken=token).execute()
        spaces += resp.get("spaces", [])
        token = resp.get("nextPageToken")
        if not token:
            return spaces


def space_members(svc, space_name):
    out, token = {}, None
    try:
        while True:
            resp = svc.spaces().members().list(
                parent=space_name, pageSize=1000, pageToken=token).execute()
            for m in resp.get("memberships", []):
                u = m.get("member", {})
                if u.get("name"):
                    out[u["name"]] = u.get("displayName") or u["name"]
            token = resp.get("nextPageToken")
            if not token:
                break
    except Exception:
        pass
    return out


def list_messages(svc, space_name, after, before, max_pages=20):
    msgs, token, pages = [], None, 0
    filt = f'createTime > "{after}" AND createTime < "{before}"'
    while True:
        resp = svc.spaces().messages().list(
            parent=space_name, pageSize=1000, pageToken=token, filter=filt).execute()
        msgs += resp.get("messages", [])
        token = resp.get("nextPageToken")
        pages += 1
        if not token or pages >= max_pages:
            return msgs


def cmd_pull(args):
    from googleapiclient.discovery import build
    creds = get_creds(interactive=False)
    if args.days:
        before = dt.datetime.now(dt.timezone.utc)
        after = before - dt.timedelta(days=args.days)
        after, before = after.strftime("%Y-%m-%dT%H:%M:%SZ"), before.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        after, before = args.after, args.before
        if not (after and before):
            sys.exit("Provide --after and --before (RFC3339, e.g. 2026-07-23T18:00:00Z) or --days N")

    svc = build("chat", "v1", credentials=creds)
    me = my_user_id(creds)
    spaces = list_spaces(svc)

    # Drop excluded (personal) spaces before any messages are fetched.
    excl_path = os.path.join(BASE, "excluded_spaces.json")
    if os.path.exists(excl_path):
        excl = json.load(open(excl_path, encoding="utf-8")).get("excluded", [])
        excl_ids = {e.get("space") for e in excl if e.get("space")}
        excl_names = {e.get("displayName") for e in excl if e.get("displayName")}
        before_n = len(spaces)
        spaces = [s for s in spaces
                  if s.get("name") not in excl_ids
                  and (s.get("displayName") or "") not in excl_names]
        if before_n != len(spaces):
            print(f"Excluded {before_n - len(spaces)} space(s) per excluded_spaces.json")
    os.makedirs(EXPORTS, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    result = {"pulled_at": stamp, "window": {"after": after, "before": before},
              "me": me, "spaces": []}
    errors, raw = [], []
    all_ids = set()
    for sp in spaces:
        name = sp.get("name")
        try:
            msgs = list_messages(svc, name, after, before)
        except Exception as e:
            errors.append({"space": name, "display": sp.get("displayName"), "error": str(e)[:200]})
            continue
        if not msgs:
            continue
        members = space_members(svc, name)
        all_ids.update(members.keys())
        all_ids.update(m.get("sender", {}).get("name", "") for m in msgs)
        raw.append((sp, msgs, members))

    names = resolve_names(creds, sorted(i for i in all_ids if i))

    def label(uid, members):
        return names.get(uid) or members.get(uid) or uid

    for sp, msgs, members in raw:
        clean = []
        for m in msgs:
            sender = m.get("sender", {}).get("name", "")
            clean.append({
                "createTime": m.get("createTime"),
                "sender": sender,
                "sender_display": label(sender, members),
                "is_me": bool(me and sender == me),
                "thread": (m.get("thread") or {}).get("name"),
                "text": m.get("text") or m.get("formattedText") or "",
                "attachments": [a.get("contentName") for a in m.get("attachment", [])],
            })
        clean.sort(key=lambda x: x["createTime"] or "")
        display = sp.get("displayName")
        if not display:
            others = [label(u, members) for u in members if u != me]
            others = [o for o in others if not o.startswith("users/")]
            display = "DM with " + ", ".join(sorted(others)[:4]) if others else "(direct message)"
        result["spaces"].append({
            "space": sp.get("name"),
            "displayName": display,
            "spaceType": sp.get("spaceType"),
            "message_count": len(clean),
            "my_message_count": sum(1 for c in clean if c["is_me"]),
            "messages": clean,
        })
    result["errors"] = errors

    jpath = os.path.join(EXPORTS, f"chat_export_{stamp}.json")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    mpath = os.path.join(EXPORTS, f"chat_export_{stamp}.md")
    with open(mpath, "w", encoding="utf-8") as f:
        f.write(f"# Google Chat export {after} -> {before}\n\n")
        for spc in sorted(result["spaces"], key=lambda s: -s["my_message_count"]):
            f.write(f"## {spc['displayName']}  ({spc['spaceType']}, "
                    f"{spc['message_count']} msgs, {spc['my_message_count']} mine)\n\n")
            for c in spc["messages"]:
                who = "**ME**" if c["is_me"] else c["sender_display"]
                text = (c["text"] or "").strip().replace("\n", " ")
                f.write(f"- {c['createTime']} {who}: {text[:600]}\n")
            f.write("\n")
        if errors:
            f.write("## Spaces that errored\n\n")
            for e in errors:
                f.write(f"- {e.get('display') or e['space']}: {e['error']}\n")
    total = sum(s["message_count"] for s in result["spaces"])
    mine = sum(s["my_message_count"] for s in result["spaces"])
    print(f"Pulled {total} messages ({mine} sent by me) across "
          f"{len(result['spaces'])} active spaces; {len(errors)} spaces errored.")
    print("JSON:", jpath)
    print("MD:  ", mpath)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    pp = sub.add_parser("pull")
    pp.add_argument("--after")
    pp.add_argument("--before")
    pp.add_argument("--days", type=int)
    args = p.parse_args()
    if args.cmd == "auth":
        get_creds(interactive=True)
    else:
        cmd_pull(args)


if __name__ == "__main__":
    main()
