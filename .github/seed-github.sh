#!/usr/bin/env bash
# seed-github.sh — project this repo's ROADMAP tasks onto GitHub, idempotently.
#
# The Markdown checklist in ROADMAP.md stays the source of truth; this script is a
# re-runnable *projection* of it. It matches existing work before creating anything
# (by a manifest entry, then by a hidden body marker), so a second run updates issues
# rather than duplicating them. Every GitHub-mutating step is guarded: a missing
# permission prints a notice and continues, downgrading the achievable tier instead of
# aborting. The tiers (richest to leanest) are A: issues + Project, B: issues +
# milestones + labels, C: this script / paste-list only — see ACCESS.md and
# PROJECT-MANAGEMENT.md.
#
# Usage:
#   ./seed-github.sh            # reconcile labels, milestone, and issues
#   DRY_RUN=1 ./seed-github.sh  # print the gh commands instead of running them
set -euo pipefail

# ----- Configuration (filled by the scaffolder) -----------------------------
REPO_SLUG="CUPIDS-Lab/co-environmental-data"      # owner/repo
MILESTONE_TITLE="L1-L2: catalog hardening & pipeline"        # first work batch (L1/L2)
MILESTONE_L3L4="L3-L4: collaboration & responsible-data"     # second work batch (L3/L4 climb)
PROJECT_TITLE="Colorado Environmental Data Hub"   # the standardized Project (see PROJECT-MANAGEMENT.md)
OWNER_DEFAULT=""                                   # default assignee; empty = leave assignment to GitHub
                                                   # (the PI owns #4/#5; the good-first-issues stay open)
LABELS_FILE="$(dirname "$0")/labels.yml"
SYNC_FILE="$(dirname "$0")/engagement-sync.json"  # task-id -> issue/item + content hash

# ----- DRY_RUN plumbing ------------------------------------------------------
DRY_RUN="${DRY_RUN:-0}"
run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf 'DRY_RUN:'; printf ' %q' "$@"; printf '\n'
  else
    "$@"
  fi
}

note()  { printf '  -- %s\n' "$*" >&2; }   # a downgrade/skip notice
fail()  { printf 'ERROR: %s\n' "$*" >&2; }  # a hard stop (only before any mutation)

# Capability flags, lowered by preflight as gaps are found.
CAN_ISSUES=1
CAN_PROJECT=1
CAN_WIKI=1

# ----- PREFLIGHT (run before mutating; never abort, just downgrade) ----------
preflight() {
  printf '== Preflight: checking access for %s ==\n' "$REPO_SLUG" >&2

  if ! command -v gh >/dev/null 2>&1; then
    fail "gh CLI not found. Install it, or use the paste-able list in engagement-issues.md (Tier C)."
    exit 1
  fi
  if ! gh auth status >/dev/null 2>&1; then
    fail "Not authenticated. Run: gh auth login  (then: gh auth refresh -s project,read:project,repo)."
    exit 1
  fi
  # Projects v2 live at org/user scope; the 'project' token scope unlocks board steps.
  if gh auth status 2>&1 | grep -qiE "Token scopes:.*\bproject\b"; then
    :
  else
    note "Missing 'project' scope -> grant it via: gh auth refresh -s project,read:project,repo"
    note "Downgrading: will create issues/labels/milestone but skip the Project (Tier B)."
    CAN_PROJECT=0
  fi
  local feats
  if feats="$(gh repo view "$REPO_SLUG" --json hasIssuesEnabled,hasWikiEnabled 2>/dev/null)"; then
    if ! grep -q '"hasIssuesEnabled":true' <<<"$feats"; then
      note "Issues are disabled on $REPO_SLUG -> enable via Settings -> Features -> Issues."
      CAN_ISSUES=0
    fi
    if ! grep -q '"hasWikiEnabled":true' <<<"$feats"; then
      note "Wiki disabled -> enable via Settings -> Features -> Wiki AND create its first page before pushing."
      CAN_WIKI=0
    fi
  else
    note "Could not read repo features (token may lack repo read) -> grant 'repo' scope; skipping wiki."
    CAN_WIKI=0
  fi
  if ! gh project list --owner "${REPO_SLUG%%/*}" >/dev/null 2>&1; then
    note "Cannot list Projects for ${REPO_SLUG%%/*} -> needs org 'Projects: Read and write' or the 'project' gh scope."
    CAN_PROJECT=0
  fi
  printf '== Preflight done: issues=%s project=%s wiki=%s ==\n' "$CAN_ISSUES" "$CAN_PROJECT" "$CAN_WIKI" >&2
}

# ----- Labels: reconcile from labels.yml -------------------------------------
seed_labels() {
  [[ "$CAN_ISSUES" == "1" ]] || { note "Skipping labels (issues unavailable)."; return 0; }
  [[ -f "$LABELS_FILE" ]] || { note "No labels.yml found at $LABELS_FILE; skipping labels."; return 0; }
  printf '== Labels ==\n' >&2
  local name="" color="" desc=""
  flush_label() {
    [[ -n "$name" ]] || return 0
    run gh label create "$name" --color "$color" --description "$desc" \
        --repo "$REPO_SLUG" --force || note "Label '$name' could not be set (permission?); continuing."
    name=""; color=""; desc=""
  }
  while IFS= read -r line; do
    case "$line" in
      "- name:"*)        flush_label; name="${line#*: }" ;;
      *"color:"*)        color="${line#*: }" ;;
      *"description:"*)  desc="${line#*: }" ;;
    esac
  done < "$LABELS_FILE"
  flush_label
}

# ----- Milestone: create if absent -------------------------------------------
seed_milestone() {
  local title="$1"
  [[ "$CAN_ISSUES" == "1" ]] || { note "Skipping milestone (issues unavailable)."; return 0; }
  printf '== Milestone: %s ==\n' "$title" >&2
  local existing
  existing="$(gh api "repos/$REPO_SLUG/milestones?state=all" \
                --jq ".[] | select(.title==\"$title\") | .number" 2>/dev/null || true)"
  if [[ -n "$existing" ]]; then
    note "Milestone '$title' already exists (#$existing); leaving as is."
  else
    run gh api -X POST "repos/$REPO_SLUG/milestones" -f "title=$title" \
        || note "Could not create milestone (permission?); continuing without it."
  fi
}

# ----- Issues: create-or-update one per task ---------------------------------
# Each task carries a stable id, embedded as a hidden marker in the issue body:
#     <!-- data-project:task=<id> -->
# Matching order: the manifest (engagement-sync.json), then a search for the marker,
# then create. This is what makes re-runs converge instead of duplicating. Assignment
# is only applied when OWNER_DEFAULT is non-empty, so the script never clobbers the
# intentionally-unassigned good-first-issues.
seed_issue() {
  local task_id="$1" title="$2" labels="$3" body="$4" milestone="${5:-$MILESTONE_TITLE}"
  [[ "$CAN_ISSUES" == "1" ]] || { note "Skipping issue '$title' (issues unavailable)."; return 0; }

  local marker="<!-- data-project:task=$task_id -->"
  local full_body="${body}"$'\n\n'"${marker}"
  local hash; hash="$(printf '%s' "$full_body" | (sha256sum 2>/dev/null || shasum -a 256) | awk '{print $1}')"

  local assignee_create=() assignee_edit=()
  if [[ -n "$OWNER_DEFAULT" ]]; then
    assignee_create=(--assignee "$OWNER_DEFAULT")
    assignee_edit=(--add-assignee "$OWNER_DEFAULT")
  fi

  local num=""
  if [[ -f "$SYNC_FILE" ]] && command -v jq >/dev/null 2>&1; then
    num="$(jq -r --arg id "$task_id" '.[$id].issue // empty' "$SYNC_FILE" 2>/dev/null || true)"
  fi
  if [[ -z "$num" ]]; then
    num="$(gh issue list --repo "$REPO_SLUG" --state all --search "$marker in:body" \
             --json number --jq '.[0].number' 2>/dev/null || true)"
  fi

  if [[ -n "$num" && "$num" != "null" ]]; then
    note "Updating issue #$num for task '$task_id'."
    run gh issue edit "$num" --repo "$REPO_SLUG" --title "$title" --body "$full_body" \
        --add-label "$labels" "${assignee_edit[@]+"${assignee_edit[@]}"}" --milestone "$milestone" \
        || note "Could not fully update #$num (permission?); continuing."
  else
    note "Creating issue for task '$task_id'."
    run gh issue create --repo "$REPO_SLUG" --title "$title" --body "$full_body" \
        --label "$labels" "${assignee_create[@]+"${assignee_create[@]}"}" --milestone "$milestone" \
        || { note "Could not create issue for '$task_id' (permission?); continuing."; return 0; }
    if [[ "$DRY_RUN" != "1" ]]; then
      num="$(gh issue list --repo "$REPO_SLUG" --state all --search "$marker in:body" \
               --json number --jq '.[0].number' 2>/dev/null || true)"
    fi
  fi
  record_sync "$task_id" "$num" "$hash"
  project_upsert_item "$task_id" "$num" "$labels"
}

# ----- Manifest: task-id -> issue/item + content hash ------------------------
record_sync() {
  local task_id="$1" num="$2" hash="$3"
  [[ "$DRY_RUN" == "1" ]] && { note "DRY_RUN: would record sync for '$task_id' (#$num)."; return 0; }
  command -v jq >/dev/null 2>&1 || { note "jq not found; skipping manifest update."; return 0; }
  [[ -f "$SYNC_FILE" ]] || echo '{}' > "$SYNC_FILE"
  local tmp; tmp="$(mktemp)"
  jq --arg id "$task_id" --arg num "$num" --arg hash "$hash" \
     '.[$id] = ((.[$id] // {}) + {issue: ($num|tonumber? // $num), hash: $hash})' \
     "$SYNC_FILE" > "$tmp" && mv "$tmp" "$SYNC_FILE"
}

# ----- Project (best effort): add item + set fields --------------------------
PROJECT_NUMBER=""
project_locate() {
  [[ "$CAN_PROJECT" == "1" ]] || return 0
  [[ -n "$PROJECT_NUMBER" ]] && return 0
  local owner="${REPO_SLUG%%/*}"
  PROJECT_NUMBER="$(gh project list --owner "$owner" --format json \
                      --jq ".projects[] | select(.title==\"$PROJECT_TITLE\") | .number" 2>/dev/null || true)"
  if [[ -z "$PROJECT_NUMBER" ]]; then
    note "Project '$PROJECT_TITLE' not found; creating it."
    run gh project create --owner "$owner" --title "$PROJECT_TITLE" \
        || { note "Could not create Project (org 'Projects: RW' missing?); skipping board steps."; CAN_PROJECT=0; return 0; }
    [[ "$DRY_RUN" != "1" ]] && PROJECT_NUMBER="$(gh project list --owner "$owner" --format json \
        --jq ".projects[] | select(.title==\"$PROJECT_TITLE\") | .number" 2>/dev/null || true)"
  fi
}
project_upsert_item() {
  local task_id="$1" num="$2" labels="$3"
  [[ "$CAN_PROJECT" == "1" ]] || return 0
  [[ -n "$num" && "$num" != "null" ]] || return 0
  project_locate
  [[ "$CAN_PROJECT" == "1" && -n "$PROJECT_NUMBER" ]] || return 0
  local owner="${REPO_SLUG%%/*}"
  local url="https://github.com/$REPO_SLUG/issues/$num"
  note "Adding issue #$num to Project '$PROJECT_TITLE' and setting fields from labels."
  run gh project item-add "$PROJECT_NUMBER" --owner "$owner" --url "$url" \
      || note "Could not add #$num to the Project; continuing."
  local pri size lvl
  pri="$(grep -oE 'priority:(high|med|low)' <<<"$labels" | head -n1 | cut -d: -f2 || true)"
  size="$(grep -oE 'size:(s|m|l)' <<<"$labels" | head -n1 | cut -d: -f2 || true)"
  lvl="$(grep -oE 'level:L[0-5]' <<<"$labels" | head -n1 | cut -d: -f2 || true)"
  [[ -n "$pri"  ]] && run gh project item-edit --owner "$owner" --project-number "$PROJECT_NUMBER" \
      --url "$url" --field Priority --value "$pri"  || true
  [[ -n "$size" ]] && run gh project item-edit --owner "$owner" --project-number "$PROJECT_NUMBER" \
      --url "$url" --field Size --value "$size"      || true
  [[ -n "$lvl"  ]] && run gh project item-edit --owner "$owner" --project-number "$PROJECT_NUMBER" \
      --url "$url" --field Level --value "L$lvl"      || true
  run gh project item-edit --owner "$owner" --project-number "$PROJECT_NUMBER" \
      --url "$url" --field Status --value "Todo"      || true
}
project_status_update() {
  [[ "$CAN_PROJECT" == "1" && -n "$PROJECT_NUMBER" ]] || return 0
  note "Posting an 'On track' status update to the Project."
  run gh project status-update "$PROJECT_NUMBER" --owner "${REPO_SLUG%%/*}" \
      --status "On track" --body "Seeded from ROADMAP.md; catalog-hardening + pipeline tasks on track." \
      || note "Could not post a status update; continuing."
}

# ----- Wiki (optional): push seeds to <repo>.wiki.git ------------------------
seed_wiki() {
  [[ "$CAN_WIKI" == "1" ]] || { note "Skipping wiki (disabled/uninitialized or token cannot push wikis)."; return 0; }
  local seeds; seeds="$(dirname "$0")/wiki-seeds"
  [[ -d "$seeds" ]] || { note "No wiki-seeds/ directory; skipping wiki."; return 0; }
  printf '== Wiki ==\n' >&2
  local tmp; tmp="$(mktemp -d)"
  if ! run git clone "https://github.com/$REPO_SLUG.wiki.git" "$tmp"; then
    note "Wiki repo not clonable yet — create its first page in the UI, then re-run. Skipping."
    return 0
  fi
  run cp "$seeds"/*.md "$tmp"/ || true
  run git -C "$tmp" add -A
  run git -C "$tmp" commit -m "Seed wiki from data-project" || note "Nothing new to commit to wiki."
  run git -C "$tmp" push origin HEAD || note "Could not push wiki (token may be fine-grained, which cannot push wikis)."
}

# ----- Main ------------------------------------------------------------------
main() {
  preflight
  seed_labels
  seed_milestone "$MILESTONE_TITLE"
  seed_milestone "$MILESTONE_L3L4"

  # --- Per-task issue create-or-update calls (mirror ROADMAP.md; full DoD lives there + in the issue) ---
  local B_VERIFY B_NREL B_MATCH B_PIPE

  IFS= read -r -d '' B_VERIFY <<'BODY' || true
9 of the 56 sources in `data/raw/colorado_environmental_data_sources.json` carry `verification_status: needs_followup` — URLs/licenses/hubs not confirmed in the June 2026 audit. Filter on `verification_status == "verified"` for anything load-bearing until resolved.

### Definition of done
- [ ] Each of the 9 `needs_followup` sources has its landing/API/hub URL confirmed live
- [ ] Specifically re-verify: Reclamation RISE URL, Larimer County GIS download hub, CoAgMet license
- [ ] Each confirmed source flipped to `verification_status: verified` (or removed with a note if dead)
- [ ] Any unstated/"verify" license resolved to a named license, or kept flagged "restricted — verify"
- [ ] Change recorded in `decision-log.md`

**Why blocking:** these sources can't be relied on (or seeded into the citation dictionary) until verified.
BODY
  IFS= read -r -d '' B_NREL <<'BODY' || true
Compilation surfaced search content claiming NREL was renamed "National Laboratory of the Rockies" with domain `nlr.gov`. Unverified and almost certainly false (`data_integrity_caveat`).

### Definition of done
- [ ] `nrel.gov` confirmed canonical against an official DOE/NREL source
- [ ] Confirm `nlr.gov` appears nowhere in the catalog or any derived dictionary
- [ ] `data_integrity_caveat` retained / updated with the verification result
- [ ] Note recorded in `decision-log.md`

**Why blocking:** a poisoned domain must never enter the Stage-A URL-match dictionary.
BODY
  IFS= read -r -d '' B_MATCH <<'BODY' || true
The Stage-A URL matcher and the prose keyword detector need two fields the catalog lacks: `match_hosts` and `match_keywords` (see `context/architecture.md` §6, nb-04).

### Definition of done
- [ ] Each source has `match_hosts`: canonical hostnames from `links.*` (scheme/`www` stripped, lowercased, deduped)
- [ ] Host+subpath rules where agencies share a host (e.g. `epa.gov`, `usgs.gov`)
- [ ] Each source has `match_keywords`: agency/dataset aliases (e.g. "SNOTEL", "EnviroScreen", "COGIS")
- [ ] Account for renames (COGCC→ECMC; GeoMAC→NIFC) and `*.hub.arcgis.com` hosts; `nlr.gov` excluded
- [ ] Matcher unit-tested against known-good / known-bad URLs

**Why blocking:** Stage-A citation detection can't run without these fields.
BODY
  IFS= read -r -d '' B_PIPE <<'BODY' || true
Stand up the reproducible-pipeline layer specified in `context/architecture.md`: the journalist→article→citation pipeline as an importable package + thin notebooks, scaffolded as stubs.

### Definition of done
- [ ] Pinned environment (uv / conda) + `pyproject.toml`
- [ ] `src/cejcorpus/` package skeleton (config, schema, storage, retrieve, extract, dictionary, detect, archive, reliability, provenance)
- [ ] Notebooks `nb-00`…`nb-09` as stubs with manual-touchpoint banners (architecture §13)
- [ ] `config.example.yaml` + `.env.example`
- [ ] `tests/` + CI dry-run; `snakemake -n` runs clean

Likely breaks into sub-issues per notebook/module. Depends on the match_hosts task for the dictionary stage.
BODY

  seed_issue "verify-needs-followup-sources" "Verify the 9 \`needs_followup\` sources in the catalog" \
    "type:data,blocking,level:L1,priority:high,size:m,good-first-issue" "$B_VERIFY"
  seed_issue "quarantine-nrel-nlr-claim" "Confirm NREL canonical domain; quarantine the spurious \`nlr.gov\` claim" \
    "type:data,blocking,level:L1,priority:high,size:s,good-first-issue" "$B_NREL"
  seed_issue "add-match-hosts-keywords" "Add \`match_hosts\` / \`match_keywords\` to the source catalog" \
    "type:data,blocking,level:L2,priority:high,size:m" "$B_MATCH"
  seed_issue "build-l2-pipeline" "Build the L2 reproducible pipeline (cejcorpus stubs)" \
    "type:pipeline,level:L2,priority:med,size:l" "$B_PIPE"

  # --- L3/L4 batch (the collaboration + responsible-data climb, 2026-06-22) ---
  local B_ONBOARD B_CEJ B_LEGAL B_CODEBOOK B_LLM B_QA

  IFS= read -r -d '' B_ONBOARD <<'BODY' || true
The L3 climb scaffolded `ROLES.md` and `.github/CODEOWNERS` with the PI holding every hat and `@brianckeegan` as the placeholder owner of every path. Onboard the undergraduate research team into those roles.

### Definition of done
- [ ] Each core role in `ROLES.md` is owned by a named person, or its gap is named in the GAP-CHECK with interim coverage + a plan
- [ ] `.github/CODEOWNERS` placeholders replaced with real team handles where a path gains a new owner
- [ ] New contributors have read `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`
- [ ] Each student has run `uv sync` in a pipeline and `uv run pytest` passes for them

Not blocking, but this is what the L3 scaffolds exist to enable.
BODY
  IFS= read -r -d '' B_CEJ <<'BODY' || true
`collaboration-protocol.md` and `ROLES.md` leave the CEJ subject-matter contact unnamed. Name a committed Center for Environmental Journalism contact who will adjudicate codebook questions.

### Definition of done
- [ ] A named CEJ contact recorded in `collaboration-protocol.md` (Coordinator section)
- [ ] That contact has reviewed the "environmental journalist" / `coverage_tier` definitions
- [ ] The communication cadence (per-semester check-in + ad-hoc adjudication) is agreed

**Why blocking:** citation coding cannot begin without a subject-matter authority to resolve definition disputes (`ROLES.md` GAP-CHECK).
BODY
  IFS= read -r -d '' B_LEGAL <<'BODY' || true
The fair-use/TDM posture and the licensed-database terms in `data-management-plan.md` §Compliance are documented but not reviewed by counsel.

### Definition of done
- [ ] CU Libraries / University Counsel has reviewed the non-consumptive-research fair-use posture (metadata + excerpts + archived links, never republished full text)
- [ ] The manual-export-only handling of Nexis Uni / NewsBank / ProQuest / Factiva is confirmed within license terms
- [ ] Any required changes folded into `data-management-plan.md`, `GOVERNANCE.md`, and `contributed-data-intake.md`
- [ ] Sign-off recorded in `decision-log.md`

**Why blocking:** gates ingesting any article text or licensed-database export.
BODY
  IFS= read -r -d '' B_CODEBOOK <<'BODY' || true
The corpus needs a versioned codebook and an inter-coder reliability process before any human coding (`context/methodology.md` §4.2).

### Definition of done
- [ ] Written definitions for every `citation_type` (6 values) and `coverage_tier`, with inclusion/exclusion criteria and >=2 worked examples each, versioned in the repo
- [ ] ~10% double-coding plan defined; calibration set prepared
- [ ] Each coder clears the Krippendorff alpha >= 0.80 threshold on a calibration batch before solo coding
- [ ] Adjudication process (third-coder / consensus; log resolution; update codebook) documented

**Why blocking:** coding cannot scale without a codebook and a cleared reliability threshold (`responsible-data-checklist.md`).
BODY
  IFS= read -r -d '' B_LLM <<'BODY' || true
The LLM-based citation detector must be validated against a hand-coded gold standard before its labels are treated as authoritative (`context/methodology.md` §4.5).

### Definition of done
- [ ] Precision/recall reported vs. a gold standard
- [ ] A verbatim quote span required for every LLM-asserted citation; quotes not found in source text are programmatically rejected
- [ ] Closed-set constraint (only catalog sources) enforced
- [ ] LLM labels promoted unreviewed only above the pre-registered precision threshold (>= 0.90); otherwise kept as human-review candidates

**Why blocking:** promoting unvalidated LLM labels as authoritative would make findings indefensible.
BODY
  IFS= read -r -d '' B_QA <<'BODY' || true
Reservoir storage (#9) is built; the remaining step is the first human-reviewed Harvard Dataverse publish. Run the L4 QA gates first.

### Definition of done
- [ ] `data-bulletproofing-checklist.md` complete (reconcile vs. agency totals; recompute; independent replicate)
- [ ] `data-quality-checklist.md` reviewed for the reservoir dataset
- [ ] First Dataverse deposit reviewed by a person and published (v1.0); DOI recorded in the pipeline README + `README.md`
- [ ] Monthly refresh confirmed to target the existing dataset as a new version (one DOI)

**Why blocking:** a DOI is permanent — nothing is published before the QA gates pass (`.skills/release-and-share`).
BODY

  seed_issue "onboard-team-roles-codeowners" "Onboard the undergraduate team into ROLES + CODEOWNERS" \
    "type:governance,level:L3,priority:high,size:m" "$B_ONBOARD" "$MILESTONE_L3L4"
  seed_issue "name-cej-sme-contact" "Name the CEJ subject-matter contact (collaboration-protocol)" \
    "type:governance,blocking,level:L3,priority:high,size:s" "$B_CEJ" "$MILESTONE_L3L4"
  seed_issue "secure-fairuse-tos-review" "Secure a fair-use / licensed-DB ToS review (CU Libraries / Counsel)" \
    "type:governance,blocking,level:L3,priority:high,size:m" "$B_LEGAL" "$MILESTONE_L3L4"
  seed_issue "fill-codebook-calibration" "Fill the codebook + run inter-coder calibration (alpha >= 0.80)" \
    "type:governance,blocking,level:L4,priority:high,size:l" "$B_CODEBOOK" "$MILESTONE_L3L4"
  seed_issue "validate-llm-detector" "Validate the LLM citation detector (precision >= 0.90; quote-span)" \
    "type:pipeline,blocking,level:L4,priority:med,size:m" "$B_LLM" "$MILESTONE_L3L4"
  seed_issue "run-qa-before-dataverse-publish" "Run the QA gates before the first reservoir Dataverse publish" \
    "type:data,blocking,level:L4,priority:high,size:s" "$B_QA" "$MILESTONE_L3L4"

  # --- QA-audit batch (findings from audits/2026-06-22-qa-audit.md) ---
  local B_RECON B_RISE B_VALUES B_KNOWN B_CATLIC B_A11Y

  IFS= read -r -d '' B_RECON <<'BODY' || true
The QA audit (`audits/2026-06-22-qa-audit.md`) found the reservoir reconciliation spot-check is **stubbed and failing**, while `pipelines/reservoir-storage/docs/survey-notes.md` claims it is "done". `data/audit/reconcile.json` carries placeholder values (`GRERESCO` expected `1.0`; a literal `NOTREAL` entry; `blue-mesa` off by ~50%), and the notebook `expected` block is commented out. Per the bulletproofing checklist this reconciliation IS the canonical pre-publication gate.

### Definition of done
- [ ] Fill `expected` in the notebook with >=2 reservoirs per source from the live agency current-storage pages (record source + date)
- [ ] `data/audit/reconcile.json` shows `match=true` for all entries; commit the passing artifact
- [ ] Remove the false "reconcile done" claim + the three inconsistent Blue Mesa anchors from `survey-notes.md`; reconcile to one verified value
- [ ] Remove the `NOTREAL` placeholder

**Why blocking:** gates the first Dataverse publish (#36); a DOI is permanent.
BODY
  IFS= read -r -d '' B_RISE <<'BODY' || true
The QA audit found `src/reservoir/parsers/reclamation_rise.py` uses `attrs.get("result") or attrs.get("value")`, so a legitimate **0.0 storage (dead pool) is coerced to None -> NA**. The CSV carries ~5,217 storage zeros and ~7,451 storage NAs with a corrupted boundary between them.

### Definition of done
- [ ] Replace the `or` with an explicit key / None check so real `0.0` survives
- [ ] Add a parser test with a `0.0` storage fixture row
- [ ] Re-run; confirm storage zero-vs-NA counts change as expected; note the delta in the data-dictionary known-issues

**Why blocking:** silently dropping real zeros corrupts the published series.
BODY
  IFS= read -r -d '' B_VALUES <<'BODY' || true
The QA audit found physically impossible values in the published CSV: an elevation of **70,235 ft** (Dillon, 1 row), **2,903 negative elevations**, and **134 negative `release_cfs`** across 4 reservoirs. The audit summary reports them but nothing flags or gates them.

### Definition of done
- [ ] Add a range / plausibility gate (e.g. CO reservoir elevation 0-15,000 ft; `release_cfs >= 0` unless documented) that flags or quarantines out-of-range rows
- [ ] Disposition the flagged rows (drop / correct / document) and record it
- [ ] Add a test asserting no out-of-range values survive to `data/processed`

**Why blocking:** impossible values in a published, citable dataset are indefensible.
BODY
  IFS= read -r -d '' B_KNOWN <<'BODY' || true
Data-integrity follow-ups from the QA audit (`audits/2026-06-22-qa-audit.md`) that are not strictly publication-blocking but should land before/with publish.

### Definition of done
- [ ] Fix the `qa_flag` join so it does not emit the literal string `"None None"` (~268k rows) / `"O None"` -- emit empty/NA
- [ ] Document the **53-built vs 138-enumerated** reservoir shortfall (404 / no-data breakdown from `fetch_errors.json`); assert an expected-non-empty set so a silent drop != real no-data
- [ ] Add a **Known issues** section to `docs/data-dictionary.md` recording every audit finding (impossible values, zeros-vs-NA, qa_flag, name-case duplication) per the data-quality checklist
- [ ] Add a cross-source name/id crosswalk note (`Blue Mesa Reservoir` vs `BLUE MESA RESERVOIR`) or document them as intentionally distinct
BODY
  IFS= read -r -d '' B_CATLIC <<'BODY' || true
NEW catalog findings from the QA audit not covered by #2 / #3 / #4:
- **License fragmentation:** 29 distinct free-text `license` strings; 16/56 sources carry unstated / "verify" / restricted licenses.
- **Schema drift:** 15/56 sources use a `links.download` sub-key that `DATA-DICTIONARY.md` does not declare.
- **2 empty `links` objects** (`wind-local-met-towers`, `minerals-local-county-gis`) -- no `landing_page`.
- Minor: DATA-DICTIONARY range examples use en-dashes while the file uses ASCII hyphens; one non-TLS `http://` download URL.

### Definition of done
- [ ] Map the free-text licenses to a controlled set (`public-domain` / `cc-by` / `cc0` / `restricted` / `verify`); triage the 16 unstated entries
- [ ] Declare `download` in the DATA-DICTIONARY `links` schema (or rename to a declared key); new vintage + dict agree
- [ ] Give the 2 empty-`links` sources a `landing_page` or a `links_unavailable`-style flag
- [ ] Fix the en-dash / hyphen doc example; verify or annotate the http-only URL

L2 catalog hardening; complements #2 (verify) and #4 (match fields).
BODY
  IFS= read -r -d '' B_A11Y <<'BODY' || true
The accessibility audit found document structure, link text, and table headers all PASS, and figures/color N/A (no charts exist yet). The one "applies now" gap is **undefined acronyms** plus two prose gaps. (A `GLOSSARY.md` was added in the audit PR; the inline first-use work + prose remain.)

### Definition of done
- [ ] Define CDSS, RISE, DWR, C-BT, SWE, TDM, OKF, UNF on first use across `README.md`, `ROADMAP.md`, `NEXT-STEPS.md`, `GOVERNANCE.md`, and the pipeline `README.md` (or link the `GLOSSARY.md`)
- [ ] Add a one-line plain-language "what we found" headline to the README summary
- [ ] State inclusive-meeting practice (notes/captions, materials in advance, async contribution) in `collaboration-protocol.md`
- [ ] Add a "tell us what you need" accessibility invitation pointing to the contact / remedy path
- [ ] (L5) alt text + colorblind-safe palettes + contrast become acceptance criteria when the Datasette + Quarto site is built

Applies-now items are doc-only; the figure/color items track to the L5 publication row.
BODY

  seed_issue "reservoir-real-reconciliation" "Reservoir: run a real reconciliation before publish (it is stubbed)" \
    "type:data,blocking,level:L4,priority:high,size:m" "$B_RECON" "$MILESTONE_L3L4"
  seed_issue "reservoir-rise-zeros-bug" "Reservoir: fix RISE zeros-vs-missing parser bug" \
    "type:pipeline,blocking,level:L4,priority:high,size:s" "$B_RISE" "$MILESTONE_L3L4"
  seed_issue "reservoir-screen-impossible-values" "Reservoir: screen impossible elevation/release values" \
    "type:pipeline,blocking,level:L4,priority:high,size:m" "$B_VALUES" "$MILESTONE_L3L4"
  seed_issue "reservoir-knownissues-and-counts" "Reservoir: qa_flag fix + record-count doc + known-issues section" \
    "type:data,level:L4,priority:med,size:m" "$B_KNOWN" "$MILESTONE_L3L4"
  seed_issue "catalog-license-and-schema-drift" "Catalog: normalize licenses + reconcile links.download schema drift" \
    "type:data,level:L2,priority:med,size:m" "$B_CATLIC" "$MILESTONE_TITLE"
  seed_issue "accessibility-glossary-and-prose" "Accessibility: define acronyms/glossary + inclusive-meeting prose" \
    "type:docs,level:L4,priority:med,size:s" "$B_A11Y" "$MILESTONE_L3L4"
  # --- end per-task calls ---

  project_status_update
  seed_wiki

  printf '== Done. ROADMAP.md remains the source of truth; this projected it onto %s. ==\n' "$REPO_SLUG" >&2
}

main "$@"
