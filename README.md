# Motchiy Discord Bot

Discordサーバーを管理・運用するための多機能Discordボットです。

## 主な機能

- **権限管理**: ユーザーごとの権限（everyone, staff, mod, admin）に基づいたコマンド制限。
- **MySQL連携**: MySQLデータベースとの接続および管理機能。
- **各種コマンド**:
    - `!help`: ヘルプを表示。
    - `!status`: 状態を確認。
    - `!perm`: 権限を確認。
    - `!dl`: ダウンロード関連機能（staff以上）。
    - `!start`, `!stop`, `!allow`, `!deny`, `!restart`: 管理・モデレーション機能（mod以上）。
    - `!startup`, `!present`: 管理者機能（admin以上）。

## セットアップ

1. **環境の準備**: Python 3.11以上が必要です。
2. **依存関係のインストール**:
   ```bash
   pip install -r requirements.txt
   ```
3. **トークンの設定**: `token.txt` ファイルを作成し、Discordボットのトークンを記述してください。
4. **設定ファイルの準備**: `settings.toml` および `mysql.toml` を適切に設定してください（初回起動時に自動生成される場合があります）。
5. **起動**:
   ```bash
   python main.py
   ```

## ライセンス
本プロジェクトは[MITライセンス](https://licenses.opensource.jp/MIT/MIT.html)の下で公開されています。
