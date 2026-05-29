# AdSense 申請ガイド

このサイトは AdSense 審査に出せる状態まで整備済みです。あとはあなたのGoogleアカウントでの操作だけ。
所要時間：**約15〜30分**（待機時間を除く）。

---

## 全体の流れ

1. PR #1 をマージ → GitHub Pagesが自動デプロイ（5〜10分）
2. Google Search Console にサイト登録（任意だが推奨）
3. Google Analytics 4 のプロパティ作成（任意だが推奨）
4. **Google AdSense でサイト申請** ← ここが本番
5. 取得した各種IDを私に伝える → 全HTMLへ一括挿入（私が実行）
6. AdSense管理画面で「コードを確認」→「審査を申請」
7. 待機（数日〜2週間）

---

## ステップ1: PR #1 をマージする

ブラウザで開く：
**https://github.com/machonaengineer/myprotein-site/pull/1**

- 差分を確認し問題なければ「Merge pull request」→「Confirm merge」
- マージ後5〜10分で https://machonaengineer.github.io/myprotein-site/ に新コンテンツが反映されます
- ライブ確認：https://machonaengineer.github.io/myprotein-site/blog/ がアクセスできればOK

---

## ステップ2: Google Search Console に登録

1. https://search.google.com/search-console/ にアクセスし、imai.ryunosuke80@gmail.com でログイン
2. 「プロパティを追加」→ 「URL プレフィックス」
3. URL に `https://machonaengineer.github.io/myprotein-site/` を入力
4. 所有権の確認方法で「HTMLタグ」を選択
5. 表示される `<meta name="google-site-verification" content="XXXX">` の **content の値** をメモする（XXXX部分のみ）

---

## ステップ3: Google Analytics 4 のプロパティ作成

1. https://analytics.google.com/ にアクセス
2. 「管理」→「プロパティを作成」
3. プロパティ名「プロテイン攻略ナビ」、業種・タイムゾーンを設定
4. データストリーム → ウェブを選択 → URL に `https://machonaengineer.github.io/myprotein-site/` を入力
5. 生成された **測定ID**（G-XXXXXXX 形式）をメモする

---

## ステップ4: Google AdSense でサイト申請

1. https://www.google.com/adsense/start/ にアクセスし、imai.ryunosuke80@gmail.com でログイン
2. 住所・支払先などのアカウント情報を登録
3. 「サイト」→「サイトを追加」で `machonaengineer.github.io/myprotein-site/` を登録
4. AdSenseが2種類の情報をくれる：
   - **AdSenseコード**（`ca-pub-XXXXXXXXXXXXXXXX` を含む `<script>` タグ）
   - **Publisher ID**（`pub-XXXXXXXXXXXXXXXX`、ads.txt用）
5. **両方の値をメモする**（特に `ca-pub-XXX` 全体）

---

## ステップ5: 取得したIDを伝える

以下のフォーマットで私に共有してください：

```
AdSenseの client ID: ca-pub-XXXXXXXXXXXXXXXX
GA4の測定ID: G-XXXXXXX
Search Console の verification token: XXXXXXXX
```

私が以下を実行します：

- 全HTMLの `<head>` に検証タグを一括挿入（`inject_head.py`）
- `ads.txt` を生成
- コミット＆プッシュ
- マージしてくれれば本番反映

---

## ステップ6: AdSenseで「審査を申請」

1. AdSense管理画面に戻り「サイト」セクションを開く
2. 該当サイトの「審査を申請」をクリック
3. AdSenseがサイトをクロールしてコードを検出
4. 検出されたら「審査中」になる

---

## ステップ7: 待機

- 通常 **数日〜2週間** で結果がメール通知
- 不承認になっても理由が示されるので、私側で対応します
- 承認後は広告ユニットを作成して任意の場所に貼り付け

---

## 申請時の注意

- **サブディレクトリ申請**: `machonaengineer.github.io` はGitHub Pagesの共有ドメインなので、トップレベルではなく `/myprotein-site/` のサブパスで申請してください
- **コンテンツ要件**: 既に168本のオリジナル記事＋FAQ＋プライバシーポリシー＋お問い合わせ完備で要件は満たしています
- **広告枠**: 申請時点では広告枠を入れる必要はありません。承認後に配置します
