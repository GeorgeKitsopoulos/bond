# AI-Assisted Maintenance Guide

## Purpose

Maintainers may use AI coding assistants to accelerate routine repository work. Repository rules, behavior contracts, and test results remain the authoritative decision criteria.

## Rules for AI-assisted changes

- keep scope small and explicit
- provide current repository context before requesting edits
- define exact allowed file lists
- define required validation commands up front
- inspect diffs manually before staging
- reject broad rewrites that were not explicitly requested
- do not allow invented capabilities or fabricated behavior claims
- do not allow public docs to drift into tool-specific prompt language

## Required checks

Required baseline checks:

- python3 -m compileall src/bond
- python3 src/bond/ai_selftest.py
- make reviewcheck

Additional checks when relevant:

- action-behavior smoke tests when routing/policy/parser/action flow changes
- public-safety path scans when source, docs, config, or deploy examples include path updates

## What not to delegate blindly

- architecture decisions
- safety policy changes
- deletion of historical analysis
- public release boundary decisions
- Gitea/GitHub milestone reconciliation

## Good change request structure

Use this checklist when preparing a scoped change request:

- current baseline
- goal
- allowed files
- forbidden changes
- required validation
- expected report
