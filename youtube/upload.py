#!/usr/bin/env python3
"""YouTube Data API v3 アップロードツール — アニメ日本史ラボ

認証情報が無い環境では DRY-RUN で動作し、
アップロードに必要な全リクエスト内容を youtube/epNN_upload_manifest.json に出力する。

認証情報 (ある場合):
  - 環境変数: YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET / YOUTUBE_REFRESH_TOKEN
  - または youtube/client_secret.json (OAuth client) + youtube/token.json

Usage:
  uv run --with google-api-python-client --with google-auth-oauthlib python \
    youtube/upload.py --episode ep01 --video video/ep01_FINAL.mp4 \
    --meta youtube/ep01.yaml --thumb youtube/thumbnails/ep01_thumb.png
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))


def load_meta(path: str) -> dict:
    try:
        import yaml
        return yaml.safe_load(open(path, encoding="utf-8"))
    except ImportError:
        # yaml 無し環境用の超簡易パーサ (このリポジトリの flat YAML 用)
        data: dict = {}
        stack = [(-1, data)]
        for raw in open(path, encoding="utf-8"):
            line = raw.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip())
            key, _, val = line.strip().partition(":")
            val = val.strip().strip('"')
            while stack and indent <= stack[-1][0]:
                stack.pop()
            parent = stack[-1][1]
            if val == "":
                parent[key] = {}
                stack.append((indent, parent[key]))
            else:
                parent[key] = val
        return data


def has_credentials() -> bool:
    if os.environ.get("YOUTUBE_REFRESH_TOKEN") and os.environ.get("YOUTUBE_CLIENT_ID"):
        return True
    return os.path.exists("youtube/client_secret.json") and os.path.exists("youtube/token.json")


def build_request(meta: dict, video_path: str, thumb_path: str | None, publish_at: str | None) -> dict:
    yt = meta.get("youtube", meta)
    body = {
        "snippet": {
            "title": yt.get("title", meta.get("title", ""))[:100],
            "description": yt.get("description", ""),
            "tags": yt.get("tags", []),
            "categoryId": "27",  # Education
            "defaultLanguage": "ja",
            "defaultAudioLanguage": "ja",
        },
        "status": {
            "privacyStatus": "private" if publish_at else yt.get("privacy", "public"),
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,  # AI生成コンテンツの申告
        },
    }
    if publish_at:
        body["status"]["publishAt"] = publish_at
        body["status"]["privacyStatus"] = "private"
    req = {
        "endpoint": "https://www.googleapis.com/upload/youtube/v3/videos",
        "method": "POST",
        "params": {"uploadType": "resumable", "part": "snippet,status"},
        "body": body,
        "video_file": video_path,
        "thumbnail": thumb_path,
        "thumbnail_endpoint": "https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={VIDEO_ID}",
    }
    return req


def dry_run(req: dict, episode: str) -> str:
    os.makedirs("youtube", exist_ok=True)
    out = f"youtube/{episode}_upload_manifest.json"
    req = dict(req)
    req["mode"] = "dry-run"
    req["note"] = "認証情報がないため未アップロード。YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN を設定すると実アップロード可能。"
    req["generated_at"] = datetime.now(JST).isoformat()
    json.dump(req, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[DRY-RUN] manifest -> {out}")
    print(json.dumps(req["body"], ensure_ascii=False, indent=2)[:1200])
    return out


def real_upload(req: dict, title: str) -> str:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    scopes = ["https://www.googleapis.com/auth/youtube.upload",
              "https://www.googleapis.com/auth/youtube"]
    if os.environ.get("YOUTUBE_REFRESH_TOKEN"):
        creds = Credentials(
            token=None,
            refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
            client_id=os.environ["YOUTUBE_CLIENT_ID"],
            client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
            scopes=scopes,
        )
    else:
        creds = Credentials.from_authorized_user_file("youtube/token.json", scopes)
    if not creds.valid:
        creds.refresh(Request())
    yt = build("youtube", "v3", credentials=creds)

    media = MediaFileUpload(req["video_file"], mimetype="video/mp4", resumable=True, chunksize=8 * 1024 * 1024)
    request = yt.videos().insert(part="snippet,status", body=req["body"], media_body=media)
    resp = None
    while resp is None:
        status, resp = request.next_chunk()
        if status:
            print(f"upload {int(status.progress() * 100)}%")
    vid = resp["id"]
    print(f"uploaded: https://www.youtube.com/watch?v={vid} (private設定: {req['body']['status']['privacyStatus']})")

    if req.get("thumbnail") and os.path.exists(req["thumbnail"]):
        yt.thumbnails().set(videoId=vid, media_body=req["thumbnail"]).execute()
        print("thumbnail set")
    return vid


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--episode", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--meta", required=True)
    p.add_argument("--thumb", default=None)
    p.add_argument("--publish-at", default=None, help="ISO8601 (JST) 指定で予約公開")
    p.add_argument("--force", action="store_true", help="認証情報チェックを無視しない (dry-run させない)")
    a = p.parse_args(argv)

    if not os.path.exists(a.video):
        print(f"video not found: {a.video}", file=sys.stderr)
        return 2

    meta = load_meta(a.meta)
    publish_at = None
    if a.publish_at:
        dt = datetime.fromisoformat(a.publish_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=JST)
        publish_at = dt.astimezone(timezone.utc).isoformat()

    req = build_request(meta, a.video, a.thumb, publish_at)
    if has_credentials() and a.force:
        vid = real_upload(req, meta.get("title", a.episode))
        json.dump({"video_id": vid, "uploaded_at": datetime.now(JST).isoformat()},
                  open(f"youtube/{a.episode}_uploaded.json", "w"), ensure_ascii=False, indent=2)
    else:
        dry_run(req, a.episode)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
