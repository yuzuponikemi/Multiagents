# Necromancy Project

バイオ計測機器（フローサイトメーター）開発のためのマルチエージェント AI システム。
人格（Persona）、知識（Context）、記憶（Memory）を動的に注入可能な汎用エージェント基盤を提供する。

## 設計思想

| 原則 | 説明 |
|------|------|
| **Single Source of Truth** | 知識の源泉は常に Obsidian（MD ファイル群）|
| **Sovereign Control** | 最終的な意思決定は常に人間が保持。AI は実行（R）と助言（C）を担当 |
| **Observability by Design** | すべての推論プロセスは Arize Phoenix で可視化・追跡可能 |
| **Hybrid Intelligence** | ローカル LLM（Ollama）によるプライバシー保護と、クラウド LLM によるフォールバック |

---

## プロジェクト構成

```
Multiagents/
├── src/multiagents/
│   ├── agent/                  # BaseAgent コア基盤
│   │   ├── base.py             # BaseAgent 本体（全モジュール統合）
│   │   ├── identity.py         # Persona MD パース・システムプロンプト構築
│   │   ├── provider.py         # LLM プロバイダー抽象化 + StructuredCaller
│   │   ├── memory.py           # 短期記憶（Checkpointer）+ 長期記憶（skills.md）
│   │   ├── context.py          # arc42 セクション注入
│   │   └── safety.py           # 物理パラメータ安全検証
│   ├── agents/                 # エージェント人格ファクトリ
│   │   ├── ghost.py            # Architect Ghost（設計専門家）
│   │   ├── coder.py            # Speedy Coder（高速実装担当）
│   │   └── analyst.py          # Lab Analyst（物理制約・統計専門）
│   ├── graphs/                 # LangGraph ワークフロー
│   │   ├── unit_review.py      # 個別コードレビュー
│   │   ├── triage.py           # JIRA チケットトリアージ
│   │   └── lab_meeting.py      # 複数エージェント議論（Virtual Meeting）
│   ├── tools/                  # 外部ツール連携
│   │   ├── jira_tool.py        # JIRA クライアント（Mock / 実接続）
│   │   └── obsidian_loader.py  # Obsidian Vault 読み込み・検索
│   ├── schemas/outputs.py      # Pydantic 構造化出力モデル
│   ├── state/graph_state.py    # LangGraph 共有ステート定義
│   ├── observability/tracing.py # Arize Phoenix トレーシング
│   ├── config.py               # 中央設定（Pydantic Settings）
│   └── cli.py                  # typer CLI エントリポイント
├── personas/                   # エージェント人格定義（MD）
├── arc42/                      # アーキテクチャドキュメント
├── _memory/                    # エージェント長期記憶（skills.md）
└── tests/                      # ユニットテスト（74 テスト）
```

---

## セットアップ

### 前提条件

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) パッケージマネージャー
- [Ollama](https://ollama.ai/) ローカル LLM ランタイム

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/yuzuponikemi/Multiagents.git
cd Multiagents

# 依存パッケージをインストール
uv sync

# Ollama モデルを準備（例）
ollama pull qwen3-next
```

### 環境変数（オプション）

すべての設定は `MA_` プレフィックスの環境変数で上書き可能。

| 環境変数 | デフォルト | 説明 |
|----------|-----------|------|
| `MA_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama サーバーの URL |
| `MA_OLLAMA_MODEL` | `qwen3-next:latest` | 使用する LLM モデル名 |
| `MA_PHOENIX_ENABLED` | `true` | Phoenix トレーシングの有効化 |
| `MA_PHOENIX_ENDPOINT` | `http://localhost:6006` | Phoenix サーバーの URL |
| `MA_OBSIDIAN_VAULT_PATH` | `./obsidian` | Obsidian Vault のパス |
| `MA_MEMORY_COMPRESSION_THRESHOLD` | `20` | メッセージ圧縮の閾値 |

---

## CLI の使い方

```bash
# コードレビュー（Ghost がレビューを実施）
multiagents review path/to/code.py

# JIRA チケットのトリアージ（Analyst が分析）
multiagents triage CYTO-101

# バーチャル会議（Coder → Ghost → Analyst の議論）
multiagents meeting "Should we add closed-loop laser power feedback control?"

# 利用可能なエージェント一覧
multiagents agents
```

### CLI オプション

```bash
# Phoenix トレーシングを無効化
multiagents review code.py --no-phoenix

# 別 PC の Ollama に接続（Multi-PC 分散）
multiagents meeting "topic" --ollama-url http://192.168.1.100:11434
```

---

## アーキテクチャ

### BaseAgent — 汎用知能の器

`BaseAgent` は 5 つのモジュールをコンポジションで統合した中核クラス。
サブクラスは不要で、異なる Persona MD ファイルを指定するだけで専門エージェントを生成する。

```
BaseAgent
├── IdentityModule    # 人格（MD → SystemPrompt）
├── LLMProvider       # モデル抽象化（Ollama / Gemini）
├── MemoryModule      # 記憶（短期 + 長期）
├── ContextModule     # 知識（arc42 セクション注入）
├── SafetyModule      # 物理ガードレール
└── Tracer            # 観測性（OpenTelemetry スパン）
```

### エージェント人格

| エージェント | 役割 | 特徴 |
|-------------|------|------|
| **Ghost** | 設計アーキテクト | ADR を引用して反論する癖。C# / 強い型付けを好む |
| **Coder** | 高速実装者 | 動くコード優先。シンプルな解を最初に提案 |
| **Analyst** | 物理制約エキスパート | レーザー・流体・光学の物理的正当性を検証 |
| **Software Architect** | ソフトウェア設計 | 信頼性とフォールトトレランスを重視 |
| **Firmware Engineer** | ファームウェア | リアルタイム制御、状態マシンを好む |

### LangGraph ワークフロー

#### 1. Unit Review（個別グラフ）

```
[コード入力] → [Ghost レビュー] → [レビュー結果]
```

単一エージェントによるコードレビュー。

#### 2. Triage（トリアージグラフ）

```
[JIRA チケット取得] → [Analyst 分析] → [トリアージ結果]
```

JIRA チケットの優先度・影響範囲・複雑度を判定。

#### 3. Lab Meeting（統合グラフ — Virtual Meeting）

```
[トピック]
  → [Coder: 案を提示]
  → [Ghost: レビュー（承認 or 差戻し）]
  → 承認? ─Yes→ [Analyst: 物理制約チェック] → [議事録]
           ─No─→ [Coder: 再提案] → ... （最大 3 ラウンド）
```

複数エージェントが役割に応じて議論し、最終的な議事録を生成する。

---

## Persona MD フォーマット

エージェントの人格は `personas/` ディレクトリ内の Markdown ファイルで定義する。

```markdown
# Agent Name

## Role
一行のロール説明

## Values
- 価値観 1
- 価値観 2

## Biases
- 思考の癖 1
- 思考の癖 2

## RACI
| Task Area | Level |
|-----------|-------|
| 領域 1 | R |
| 領域 2 | C |

## Background
自由記述の背景情報
```

新しいエージェントの追加は、MD ファイルを作成して `arc42/_section_map.yaml` にロールマッピングを追記するだけでよい。コードの変更は不要。

---

## 記憶システム

### 短期記憶（Short-term / Episodic）

LangGraph の `MemorySaver` によるスレッド単位の会話コンテキスト。
メッセージ数が閾値（デフォルト 20）を超えると、LLM による要約圧縮が自動実行される。

### 長期記憶（Long-term / Reflective）

各エージェント固有の `_memory/{agent_id}_skills.md` ファイル。
タスク完了後に「教訓（Lesson Learned）」を抽出し、タイムスタンプ付きで追記する。

```python
agent.save_lesson("Always check interlock before laser activation")
agent.reload_system_prompt()  # 次回から教訓がプロンプトに反映
```

---

## 物理安全ガードレール

フローサイトメーターの物理的操作に対する安全検証。

| パラメータ | 安全範囲 | 単位 |
|-----------|---------|------|
| レーザー出力 | 0 - 100 | mW |
| 流量 | 1 - 100 | uL/min |
| PMT 電圧 | 0 - 1,000 | V |
| 圧力 | 0 - 30 | PSI |

禁止操作: `disable_interlock`, `override_safety`, `bypass_calibration`

```python
result = agent.check_safety("set_laser", {"laser_power_mw": 50})
# SafetyCheckResult(is_safe=True, reason="OK", violations=[])

result = agent.check_safety("set_laser", {"laser_power_mw": 150})
# SafetyCheckResult(is_safe=False, violations=["laser_power_mw=150 out of safe range [0, 100]"])
```

---

## 観測性（Observability）

[Arize Phoenix](https://phoenix.arize.com/) によるトレーシング。

```bash
# Phoenix サーバーを起動
phoenix serve

# トレース付きでコマンドを実行
multiagents review code.py

# http://localhost:6006 でトレースを確認
```

各スパンには以下のタグが付与される:

- `agent.id` — エージェント識別子
- `agent.model_provider` — 使用 LLM プロバイダー
- `agent.task_type` — タスク種別

---

## 構造化出力

LLM の出力を Pydantic モデルで強制。スキーマ違反時は自己修正ループ（最大 2 回リトライ）を回す。

| モデル | 用途 |
|-------|------|
| `CodeReviewResult` | コードレビュー（summary, issues, suggestions, severity）|
| `TriageResult` | JIRA トリアージ（priority, category, affected_subsystems）|
| `ReviewVerdict` | Ghost の審査（approved, feedback, adr_references）|
| `MeetingMinutes` | 会議議事録（decision, reasoning, dissents, action_items）|
| `SafetyAssessment` | 安全評価（is_safe, risk_level, mitigations）|
| `TaskReflection` | 自己省察（task_summary, lessons_learned, confidence）|

---

## テスト

```bash
# 全テスト実行（74 テスト、LLM 不要）
uv run pytest tests/ -v

# リント
uv run ruff check src/ tests/
```

### テストカバレッジ

| テストファイル | 対象 | テスト数 |
|--------------|------|---------|
| `test_identity.py` | Persona MD パース、プロンプト構築 | 8 |
| `test_context.py` | arc42 セクション読み込み | 5 |
| `test_provider.py` | LLM 抽象化、StructuredCaller リトライ | 7 |
| `test_safety.py` | パラメータ範囲検証、禁止操作 | 9 |
| `test_memory.py` | 短期・長期記憶、圧縮 | 9 |
| `test_observability.py` | Phoenix スパン属性 | 2 |
| `test_base_agent.py` | BaseAgent 統合 | 6 |
| `test_agents.py` | エージェントファクトリ | 3 |
| `test_tools.py` | JIRA Mock、Obsidian Loader | 16 |
| `test_graphs.py` | ワークフロー（review, triage, meeting）| 7 |
| `test_cli.py` | CLI コマンド | 3 |

---

## Multi-PC 分散実行

2 台の PC 間でエージェントを分散配置可能。

```
PC 1 (メイン): 開発機 + Ghost（重い推論）
PC 2 (サブ):   Coder + Analyst

# PC 2 の Ollama に接続
multiagents meeting "topic" --ollama-url http://192.168.1.100:11434
```

環境変数で恒久的に設定する場合:

```bash
export MA_OLLAMA_BASE_URL=http://192.168.1.100:11434
```

---

## 運用サイクル（Ghost Feedback Loop）

```
[トリガー]              JIRA ステータス変更、PR 作成
    ↓
[実行]                  LangGraph ワークフロー実行
    ↓
[観測]                  Arize Phoenix でトレース監視
    ↓
[レビュー]              人間がレビュー
    ├─ 承認 →           そのまま採用
    └─ 修正 →           AI に修正指示 + skills.md に教訓を記録
    ↓
[改善]                  skills.md を基にプロンプトを微調整
```

---

## 将来の拡張

- **GeminiProvider**: クラウド LLM フォールバック（ローカル推論失敗時の自動切替）
- **Digital Ghost**: 退職メンバーの「思考の癖」を Persona ファイルで再現
- **Hybrid RAG**: ベクトル検索による大規模ドキュメント検索
- **Real JIRA 接続**: `JiraClient` ABC の実装を差し替えるだけで本番接続可能
- **RPC 分散**: 複数 PC 間のエージェント連携を RPC で実現

---

## 技術スタック

| カテゴリ | ツール |
|---------|-------|
| 言語 | Python 3.11+ |
| パッケージ管理 | uv |
| LLM フレームワーク | LangChain / LangGraph |
| ローカル LLM | Ollama |
| 構造化出力 | Pydantic v2 |
| 設定管理 | pydantic-settings |
| 観測性 | Arize Phoenix / OpenTelemetry |
| CLI | typer |
| テスト | pytest |
| リンター | ruff |

---

## ライセンス

Private
